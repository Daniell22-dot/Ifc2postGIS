**ER Diagram (Mermaid - view in compatible viewer):**
```mermaid
erDiagram
    ifc_site
    ifc_building
    ifc_storey
    ifc_space
    ifc_site ||--o{ ifc_building : "1:m"
    ifc_building ||--o{ ifc_storey : "1:m"
    ifc_storey ||--o{ ifc_space : "1:m"
```
