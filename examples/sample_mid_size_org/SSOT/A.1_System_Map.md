# A.1 System Map
Version: 0.1.0  
Owner: Technology & Operations  

---

## System Overview

The organization operates a hybrid system composed of
physical POS systems and centralized digital services.

---

## Architecture Style

Hybrid (legacy POS + centralized digital services)

---

## Modules / Systems

| Name | Type | Responsibility |
|-----|------|----------------|
| POS System | External | In-store orders and payments |
| Digital Ordering Platform | Service | Online orders |
| Menu Management Service | Service | Menu and pricing |
| Inventory System | Service | Stock tracking |
| Payment Gateway | External | Payments |
| Delivery Platforms | External | Last-mile delivery |

---

## Key Data Stores

- POS databases
- Central product database
- Inventory database

---

## External Dependencies

- Payment providers
- Delivery aggregators
- ERP system

---

## Critical System Flows

- Order creation → fulfillment
- Menu update → channel propagation
- Inventory update → availability

---

## Known Gaps / Drift

- Manual overrides in stores
- Delayed inventory updates

---

## Linked Artifacts

- A.4 Data Entities
- P.1 Product Map