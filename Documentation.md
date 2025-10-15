## How to run
```python
streamlit run interface.py
```

## Syntax

### Node Operations

#### **CREATE**
Create new nodes with properties:
```sql
CREATE (Morgoth:Character{Species:Valar, Power:Infinite})
CREATE (Sauron:Character{Species:Maiar, Master:Morgoth})
```

#### **READ**
```sql
-- Read all nodes
READ ()

-- Read by ID
READ (Frodo)

-- Read by class
READ (:Hobbit)

-- Read with property filter
READ (:Character) WHERE Species = Hobbit

-- Read with multiple filters
READ (:Character) WHERE Species = Elf AND Realm = Lothlorien
```

#### **UPDATE**
```sql
UPDATE (Frodo:Hobbit{Location:Mordor})
UPDATE (Gandalf{Color:White}) WHERE Color = Grey
```

#### **DELETE**
```sql
DELETE (Morgoth)
DELETE (:Character) WHERE Species = Orc
```


### Edge Operations
#### **CREATE**
```sql
CREATE [Morgoth, Sauron:is_the_master{Years:1000}]
CREATE [Frodo, Ring:bears{Duration:Temporary}]
```

#### **READ**
```sql
-- Read all relationships
READ []

-- Read a specific relationship
READ [Frodo, Sam]

-- Read relationships by type
READ [:FRIENDS_WITH]

-- Read with properties
READ [:ALLIES_WITH] WHERE status = strong
```

#### **UPDATE**
```sql
UPDATE [Frodo, Sam:FRIENDS_WITH{Trust:Unbreakable}]
```

#### **UPDATE**
```sql
DELETE [Frodo, Ring]
DELETE [:BETRAYS]
```

### Path Operations
#### **LINK**
```sql
-- Find shortest path
LINK [Frodo, Mordor]

-- Find all paths
LINK [Gollum, Ring] ALL

-- Find paths with maximum length
LINK [Gandalf, Frodo] MAX_LENGTH 3
```

You can now specify minimum and maximum path lengths:
```sql
LINK [Frodo, Saruman] MIN_LENGTH 3
LINK [Frodo, Saruman] MAX_LENGTH 5
LINK [Frodo, Saruman] MIN_LENGTH 3 MAX_LENGTH 5
```

### Visualize Operations
#### **COLOR/CLUSTER**
These commands control graph clustering and colorization.

To apply clustering or colorization:
```sql
CLUSTER
COLOR
```

To remove clustering or colorization and revert to the original state:
```sql
CLUSTER NOT
COLOR NOT
```

### Linearization
#### **LINEARISE**
Transform all graph triples into text for NLP usage or debugging.
```sql
LINEARISE
```

To hide the linearized text section:
```sql
LINEARISE NOT
```

### Examples
```sql
-- Create a new character
CREATE (Bilbo:Hobbit{Age:111, Home:"Bag End"})

-- Find all Hobbits
READ (:Hobbit)

-- Find characters from the Shire
READ (:Character) WHERE Home = "The Shire"

-- Update Gandalf's status
UPDATE (Gandalf{Color:White}) WHERE Color = Grey

-- Delete Gollum
DELETE (Gollum)


-- Create friendship
CREATE [Merry, Pippin:FRIENDS_WITH{Since:Childhood}]

-- Find all alliances
READ [:ALLIES_WITH]

-- Find strong relationships
READ [:FRIENDS_WITH] WHERE Trust = High

-- Update relationship
UPDATE [Frodo, Sam:FRIENDS_WITH{Loyalty:Unbreakable}]

-- Delete betrayal
DELETE [Saruman, Gandalf]


-- Find path from Frodo to Mordor
LINK [Frodo, Mordor]

-- Find all paths between Gollum and the Ring
LINK [Gollum, "The One Ring"] ALL

-- Find short paths between locations
LINK [Rivendell, Mordor] MAX_LENGTH 3
```