# A.4 Data Entities
Version: 0.1.0  
Owner: Technology  

---

## Entity Registry

| Entity | Description | Source of Truth |
|------|-------------|----------------|
| Customer | End user | Digital Platform |
| Order | Purchase transaction | POS / Digital |
| Menu Item | Sellable product | Menu Service |
| Inventory Item | Stock unit | Inventory System |
| Restaurant | Physical location | ERP |
| Payment | Financial transaction | Payment Gateway |

---

## Relationships

- Customer places Order
- Order contains Menu Items
- Menu Items consume Inventory Items
- Order processed by Restaurant
- Order generates Payment

---

## Data Constraints

- Menu consistency across channels
- Inventory accuracy per location
- PII handling for customer data

---

## Known Gaps

- Duplicate customer records
- Inventory reconciliation delays