**ER Diagram (Mermaid - view in compatible viewer):**
```mermaid
erDiagram
    ifc_site {
        id
        global_id
        name
        geom
    }
    ifc_building {
        id
        global_id
        name
        site_global_id
    }
    ifc_storey {
        id
        global_id
        name
        elevation
        building_global_id
    }
    ifc_space {
        id
        global_id
        name
        long_name
        storey_global_id
    }
    ifc_site ||--o{ ifc_building : "1:m"
    ifc_building ||--o{ ifc_storey : "1:m"
    ifc_storey ||--o{ ifc_space : "1:m"
```
```