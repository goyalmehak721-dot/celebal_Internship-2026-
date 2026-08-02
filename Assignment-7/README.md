# Project Summary — Incremental Data Processing with Delta Lake

## Objective
Perform incremental data processing using Delta Lake: load a dataset into a Delta table,
clean it, simulate a batch of incremental (new/updated) data, merge that batch in, and
validate the result.

## Dataset
`Superstore2.csv` — a retail orders dataset, 9,994 rows x 21 columns (order, customer,
product, sales, quantity, discount, and profit details for each order line).

**Data quality note:** the dataset is otherwise clean (no missing values, no duplicate
rows), but the `Order Date` and `Ship Date` columns mix two separator styles —
some rows use `M-D-YYYY`, others `M/D/YYYY` — which needs to be normalized to a single
format before the dates can be parsed reliably.

## What was done
1. **Loaded into a Delta table** — the CSV was read and written out as a managed Delta
   table, giving it Delta Lake's transaction log, versioning, and ACID guarantees from
   that point on.
2. **Basic cleaning** — checked for and handled nulls and duplicate rows (none were
   found), and normalized the two mixed date-separator styles into one consistent format.
3. **Simulated an incremental batch** — built a second dataset representing a typical
   incremental load:
   - **200 updates**: existing orders re-sampled with a revised `Sales`/`Profit` (simulating
     a late correction), matched back to the original rows by `Row ID`.
   - **150 inserts**: brand-new orders with fresh `Row ID`s and `Order ID`s.
4. **Applied a MERGE** — used Delta Lake's `MERGE INTO` (matched on `Row ID`) to update the
   200 matching rows in place and insert the 150 new ones in a single atomic operation.
5. **Validated the result**:

   | Check | Result |
   |---|---|
   | Row count before merge | 9,994 |
   | Row count after merge | 10,144 (9,994 + 150 inserted) |
   | Duplicate `Row ID`s after merge | 0 |
   | Spot-checked updated row reflects new `Sales` value | Confirmed |

6. **Displayed the final dataset and summary** — the merged table was inspected, and Delta
   Lake's transaction history (`DESCRIBE HISTORY`) shows two versions: the initial load and
   the merge, giving a full audit trail of what changed and when.

## Outcome
The merge behaved exactly as expected: every matched row was updated in place, every
unmatched row was inserted, no duplicate keys were introduced, and the row count math
checked out precisely (9,994 → 10,144). Delta Lake's versioned transaction log means this
whole operation — including the intermediate cleaning step — is fully auditable after the
fact.

## Why Delta Lake here
A plain CSV overwrite would have destroyed the history of the incremental load and offered
no way to distinguish "updated" rows from "unchanged" rows without a manual diff. Delta
Lake's `MERGE INTO` handles both cases (update vs. insert) in one atomic statement, and its
transaction log gives a built-in audit trail — the two capabilities this exercise is meant
to demonstrate.
