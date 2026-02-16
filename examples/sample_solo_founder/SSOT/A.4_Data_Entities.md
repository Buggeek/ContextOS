# A.4 Data Entities
Version: 0.1.0  
Owner: Founder  

---

## Entity Registry

| Entity | Description | Source of Truth |
|------|-------------|----------------|
| User | Registered user | Database |
| Session | User session | Auth provider |
| Core Item | Main business object | Database |

---

## Relationships

- User owns Core Items
- User has Sessions

---

## Data Constraints

- Basic PII protection
- Data integrity over performance

---

## Known Gaps

- Future billing entities not defined yet