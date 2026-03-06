# A.1 System Map
## Version: 0.1.0
Last Updated: 2026-02-19  
Owner: Technology & Operations  

---

## Purpose

Make the system visible. Define modules/systems and boundaries at a high level so that changes can be reasoned about across physical and digital operations.

## System Overview

The organization operates a hybrid system composed of
physical POS systems and centralized digital services.

---

## Architecture Style

Hybrid (legacy POS + centralized digital services)

---

## Modules / Systems

| Name | Type | Responsibility | Owned By | Notes |
|------|------|----------------|----------|------|
| POS System | External | In-store orders and payments | Restaurant locations | Legacy constraints vary by location |
| Digital Ordering Platform | Service | Online orders | Digital product team | Canonical digital order intake |
| Menu Management Service | Service | Menu and pricing | Central ops + digital | Must propagate to all channels |
| Inventory System | Service | Stock tracking | Operations | Per-location inventory accuracy |
| Payment Gateway | External | Payments | Finance + digital | PCI/compliance constraints |
| Delivery Platforms | External | Last-mile delivery | Operations | API/webhook integration risk |

---

## Key Data Stores

| Name | Type | Owned By | Notes |
|------|------|----------|------|
| POS databases | DB | Restaurant locations | Not centrally governed |
| Central product database | DB | Digital product team | Menu + catalog-related source |
| Inventory database | DB | Operations | Location-level stock truth |

---

## External Dependencies

| Provider/System | Purpose | Interface | Risk Notes |
|----------------|---------|----------|-----------|
| Payment providers | Process customer payments | API | Regulatory + operational impact |
| Delivery aggregators | Last-mile delivery | API/webhook | Integration drift + SLA variability |
| ERP system | Corporate data + restaurant registry | Export/API (varies) | Data latency and ownership ambiguity |

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

---

## Change Log
- 2026-02-19 — v0.1.0 — Initial creation