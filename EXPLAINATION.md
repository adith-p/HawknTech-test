# EXPLANATION.md

## Thought Process

I split the project into 2 parts — `api` and `core`. This was to segment the moving parts
into isolated environments. `api` will handle and route all the URL patterns and endpoints,
while `core` will handle all the current required endpoint views, serializers, etc.

I thought about segmenting them even further but that seemed not required and overkill, so
I decided to keep it under umbrella apps given the count of the endpoints.

---

## Models

I implemented the models based on the assessment requirements. I made sure to keep very
minimal fields for all the models.

Thing to note here is that I created an abstract model which will be inherited by all other
models, called `TimestampedModel`, which will have 3 fields: `id` (UUID), `created_at`,
`updated_at`.

Core takeaways from each model:

**Branch**
- Branch has 3 fields to attempt to keep it minimal: `name`, `code`, `admin`
- `code` is a unique field which will act as a unique identifier for external use cases
  such as endpoints where you want to query branches
- `admin` is a FK to the abstract user model
- `name` is just a normal identifier — since `id` and `code` exist, the burden of
  uniqueness is not on the name

**Product**
- Has 2 fields: `name` and `sku`
- `sku` will be a unique identifier which will be auto-generated using a support method
  that uses Python's `secrets` lib

**Stock**
- Tracks available quantity per product per branch
- Modeled as a mapping between `Branch` and `Product`
- Fields: `branch` (FK), `product` (FK), `quantity`
- The model has a `unique_together` on `(branch, product)` so each product has exactly
  one stock row per branch. This avoids duplication and makes updates straightforward
  during transfers.

**StockTransfer**
- This is the largest model when compared with the others
- Contains: `from_branch`, `to_branch`, `product`, `quantity`, `requested_by`,
  `approved_by`, `approved_at`, `transfer_status`, `transfer_type`
- This model is the cornerstone which facilitates the following: track history, support
  the approval flow, keep auditability

---

## Design Pattern

Before we move on to concurrency and atomicity, let me share the design pattern I chose.

I initially decided to use `fat serializers and skinny views` but then I decided to move
towards handing over the core flow to the **service layer**. Why? Because this way we can
create service classes which will be helpful when scaling the app, when adding new
endpoints or features, and more importantly for reusability and less maintenance overhead.

I also created a utils method so that I can get the same JSON response structure every time
for errors, called `APIErrorResponse`.

Views only handle the return of responses from the service layer.

### Authorization — Two Levels, Two Checks

Right now the system has two levels of roles: `branch_admin` and `user`.

The authorization is enforced at two distinct levels:

**1. Class-level check — `IsBranchAdmin` permission class**

This is a DRF permission class that runs on every request before anything else. It checks
two things: that the user is authenticated, and that the user's role is `branch_admin` for
any write operation. Read operations (GET, HEAD, OPTIONS) are allowed through for any
authenticated user. This is the gate at the door.

**2. Object-level check — service layer ownership validation**

Passing the class-level check is not enough. Inside the service layer, there is a second
check that runs against the actual data. For example, even if you are a `branch_admin`,
you cannot create a `REQUEST` transfer unless you are the admin of the `to_branch`, and
you cannot approve it unless you are the admin of the `from_branch`. The roles are
enforced not just by what you are, but by what you own.

These two levels together make sure that role and ownership are both validated on every
write operation.

### Idempotency

I did think about implementing explicit idempotency via an idempotency key or a request ID
header. The initial thought process was to use a middleware that intercepts the request,
checks for the key, and either caches the response or stores it in the DB so repeated
requests with the same key return the same result without re-executing the operation.

But I decided against it. It would introduce a fair amount of overhead — middleware,
caching or DB storage, key management — and for this assessment we only really need to
cover two endpoints. That complexity felt unjustified.

Instead I handled idempotency at the service layer, which is a cleaner fit here:

- **On transfer creation** — there is a `UniqueConstraint` at the DB model level on
  `(from_branch, to_branch, product, quantity)` where `transfer_status = PENDING`. So if the same
  request comes in twice, the second one hits the constraint and gets bounced. No duplicate
  pending transfers can exist for the same branch–product pair.

- **On transfer approval** — the service layer checks whether the transfer is still
  `PENDING` before doing anything. If it has already been processed, the request is
  rejected immediately. So repeated approval attempts on the same transfer are a no-op
  from the data perspective.

Both of these are enforced at the right layer without any additional infrastructure.

---

## Transactions, Concurrency & Query Optimization

I used `transaction.atomic` from Django to mark the transaction and avoid partial updates
whenever possible.

I used locking (`select_for_update`) to make sure the row is locked and avoid conflicts.

I also implemented cursor pagination on one of the endpoints rather than offset, so that
it's not heavy on the DB and services when querying data of thousands of records — and the
endpoint won't break even if the data is too much.

To avoid the N+1 problem I optimised the queries using `select_related`, so we don't fetch
unnecessarily and fetch everything in one go.

---

## Core Feature — Two-Way Transfer Model

Initially the stock transfer process followed a request–approval cycle. For example, if
Branch B required stock, it had to send a request to Branch A. Only after Branch A approved
the request would the stock be transferred.

This approach was later changed to support a more flexible two-way transfer model by
introducing a `transfer_type` — either `REQUEST` or `OFFER`.

The limitation of the earlier system was that even when Branch A had surplus stock and
wanted to send it to Branch B, it could not do so unless Branch B explicitly initiated a
request. This made the process inefficient and did not reflect real-world operational needs.

To address this, an offer-based flow was introduced. In this model, if Branch A wants to
send stock to Branch B, it can create a transfer entry with the transfer type set to
`OFFER`, without waiting for a prior request.

This change primarily affects the approval logic:

- If the transfer type is `OFFER`, the receiving branch (the `to_branch`) is responsible
  for approving the transfer.
- If the transfer type is `REQUEST`, the sending branch (the `from_branch`) is responsible
  for approval.

---

## Trade-offs & Unfinished Work

- The assessment allowed React as an optional extra. I chose to invest my time in backend reliability – transactions, concurrency, tests, and API design – because that’s where the core business logic lives and where I can deliver the most value.

- currently the system does not support idempotency via an explicit key or header, but it does handle it at the service layer through DB constraints and status checks. This is a trade-off that simplifies the implementation while still preventing duplicate operations.

- **Expand the role model to three levels.** Right now we have two roles — `branch_admin`
  and `user`. Going forward I would introduce a third level, something like a global admin
  or a regional admin, who would have visibility and control across multiple branches rather
  than being scoped to one. This would also naturally lead to scoping transfer records to
  the logged-in user — right now any authenticated user can list all transfers, but with a
  proper role hierarchy you'd scope what each role can see based on what they own or manage.
