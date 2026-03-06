# A.4 Data Entities
## Version: 0.1.0
Last Updated: 2026-02-19  
Owner: Technology  

---

## Purpose

Define the core business entities and how they relate across physical and digital channels.

## Entity Registry

| Entity | Description | Source of Truth (System) | Key Fields | PII? (Y/N) | Notes |
|--------|-------------|--------------------------|------------|------------|------|
| Customer | End user | Digital Ordering Platform | customer_id, contact, preferences | Y | Duplicate risk across channels |
| Order | Purchase transaction | POS / Digital Ordering Platform | order_id, items, totals, status | N | Cross-channel reconciliation needed |
| Menu Item | Sellable product | Menu Management Service | sku, name, price, availability | N | Must be consistent across channels |
| Inventory Item | Stock unit | Inventory System | item_id, location_id, quantity | N | Per-location accuracy is critical |
| Restaurant | Physical location | ERP | restaurant_id, address, hours | N | Governs operational constraints |
| Payment | Financial transaction | Payment Gateway | payment_id, amount, status | N | PCI boundaries apply |

---

## Relationships

- Customer places Order
- Order contains Menu Items
- Menu Items consume Inventory Items
- Order processed by Restaurant
- Order generates Payment

---

## Ownership Boundaries

- POS data is locally managed per restaurant location; central teams cannot assume consistency.
- Menu entities are centrally governed but must propagate to all channels.
- Inventory entities are operational truth and require reconciliation routines.
- Payment entities are governed by finance/compliance constraints.

---

## Data Constraints

- Menu consistency across channels
- Inventory accuracy per location
- PII handling for customer data

---

## Linked Artifacts

- A.1 System Map
- P.1 Product Map
- G.1 Definition of Ready
- G.2 Definition of Done

---

## Known Gaps

- Duplicate customer records
- Inventory reconciliation delays

---

## Change Log
- 2026-02-19 — v0.1.0 — Initial creation