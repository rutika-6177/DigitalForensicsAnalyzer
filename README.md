# 🛡️ AegisForensics

> **A Digital Evidence Custody, Deduplication & Relationship Analysis System**
> Built entirely in **C++17** with custom Data Structures — Hash Table, Red-Black Tree, and Relationship Graph — paired with a Cyberpunk HUD web interface.

---

## 📌 What Is This?

**AegisForensics** is a forensic image evidence management system. When an investigator uploads images, the system:

1. Computes **SHA-256**, **MD5**, and a **64-bit perceptual fingerprint** for each file.
2. Classifies it as one of three states:
   - 🔴 **Exact Duplicate** — byte-for-byte identical (SHA-256 match)
   - 🟡 **Structurally Identical** — visually same despite compression, resize, or format change (Hamming distance ≤ 10 on perceptual fingerprint)
   - 🟢 **Unique Evidence** — new, distinct file
3. Indexes the record across **three custom data structures** simultaneously.
4. Builds a live **relationship graph** showing which files are related.
5. Allows soft-deletion into a **Quarantine Vault** — files are never permanently destroyed.
6. Provides 1-click **recovery** to restore quarantined evidence back into active custody.

---

## 🧠 Data Structures Used (Custom C++17 Implementations)

| Structure | File | Role | Complexity |
| :--- | :--- | :--- | :--- |
| **Separate-Chaining Hash Table** | `src/dsa/hash_table.hpp` | Exact-duplicate detection via SHA-256 lookup | O(1) average |
| **Red-Black Tree** | `src/dsa/red_black_tree.hpp` | Chronological evidence index for timeline & range queries | O(log n) worst-case |
| **Adjacency List Graph** | `src/dsa/graph.hpp` | Evidence relationship mapping with BFS/DFS cluster detection | O(|V| + |E|) |

No STL containers (map, unordered_map, set) are used for the core forensic logic — all three are built from scratch.

---

## 🔍 How Duplicate Detection Works

```
Upload Image
     │
     ▼
Compute SHA-256 + MD5 + 64-bit Perceptual Fingerprint
     │
     ▼
Query Hash Table ──── SHA-256 match found? ──→ EXACT DUPLICATE
     │
     │ (no match)
     ▼
Compare perceptual fingerprint against all active records
Hamming distance = popcount(H1 XOR H2)
     │
     ├── distance ≤ 10 ──→ STRUCTURALLY IDENTICAL  (edge weight = 1 - d/64)
     │
     └── distance > 10 ──→ UNIQUE EVIDENCE
     │
     ▼
Insert into Hash Table + Red-Black Tree + Graph
Save binary to storage/images/ (UUID filename)
Commit metadata to database/forensic.json
```

**Perceptual Fingerprint algorithm (Average Hash):**
1. Decode image pixels via `stb_image`
2. Convert to grayscale, downsample to 8×8
3. Compute mean luminance p̄ across all 64 pixels
4. Set bit i = 1 if pixel_i > p̄, else 0 → produces a 64-bit `uint64_t`
5. Hamming distance between two fingerprints = number of differing bits

---

## 🗂️ Project Structure

```
ds/
├── src/
│   ├── main.cpp                        # Server entry point
│   ├── dsa/
│   │   ├── evidence_record.hpp         # Evidence entity (UUID, hashes, timestamps, soft-delete fields)
│   │   ├── hash_table.hpp              # Custom separate-chaining hash table
│   │   ├── red_black_tree.hpp          # Custom self-balancing RB-tree
│   │   └── graph.hpp                   # Custom adjacency-list graph
│   ├── hashing/
│   │   ├── sha256.hpp / sha256.cpp     # SHA-256 implementation (FIPS 180-4)
│   │   ├── md5.hpp / md5.cpp           # MD5 implementation (RFC 1321)
│   │   └── phash.hpp / phash.cpp       # 64-bit average perceptual hash + Hamming distance
│   ├── engine/
│   │   └── forensic_engine.hpp / .cpp  # Orchestrates ingestion, deduplication, recovery
│   ├── storage/
│   │   ├── storage_interface.hpp       # Abstract storage contract
│   │   └── local_storage.hpp / .cpp    # Binary file store + JSON metadata persistence
│   └── server/
│       └── http_server.hpp / .cpp      # WinSock REST API + static file server
├── ui/
│   ├── index.html                      # Cyberpunk HUD interface
│   ├── style.css                       # Neon/glassmorphic styling
│   └── script.js                       # Force-directed graph, dossier modals, recovery vault
├── include/
│   ├── httplib.h                       # Single-header C++ HTTP server
│   ├── json.hpp                        # nlohmann/json
│   ├── stb_image.h                     # Single-header image decoder
│   └── stb_image_resize2.h             # Image resampler
├── tests/
│   └── test_dsa_engine.cpp             # 7-suite automated test runner
├── database/
│   └── forensic.json                   # Persistent evidence metadata store
├── storage/
│   └── images/                         # Binary evidence files (never deleted)
├── build.bat                           # Compile with GCC 12 / Cygwin
├── run.bat                             # 1-click build + launch + open browser
└── README.md
```

---

## 🚀 Running the Application

### Quickest Way — Double-click `run.bat`

```powershell
.\run.bat
```

This will:
1. Compile `aegis_server.exe` using GCC 12 (`-std=c++17 -O2`) if not already built
2. Start the HTTP server on port `8080`
3. Automatically open `http://localhost:8080/` in your default browser

### Manual Steps

```powershell
# 1. Compile
.\build.bat

# 2. Run server
.\aegis_server.exe

# 3. Open browser at
#    http://localhost:8080/
```

### Run Tests

```powershell
.\build.bat test
.\test_runner.exe
```

---

## 🌐 REST API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Ingest image; returns classification + hashes |
| `GET` | `/api/evidence` | List all active evidence records |
| `GET` | `/api/evidence/:id` | Full forensic dossier for one record |
| `DELETE` | `/api/evidence/:id` | Soft-delete → moves to quarantine vault |
| `POST` | `/api/recover/:id` | Restore quarantined evidence to active custody |
| `GET` | `/api/deleted` | List all quarantined (soft-deleted) records |
| `GET` | `/api/graph` | Node + edge payload for the relationship graph |
| `GET` | `/api/stats` | Vault statistics (totals, storage saved, duplicates) |
| `GET` | `/images/:filename` | Serve stored image binary |

---

## 🖥️ Interface Features

| Feature | Description |
| :--- | :--- |
| **Drop Zone Uploader** | Drag-and-drop or click to upload images |
| **Session / Vault Counter** | Shows `0 / N in Vault` — session resets on refresh, vault total persists |
| **Relationship Graph** | Force-directed canvas graph with exponential cooling (α × 0.93/frame); settles in ~1.5s |
| **Evidence Table** | Sortable, filterable table with hash display and thumbnails |
| **Forensic Dossier** | Click any evidence to see SHA-256, MD5, pHash, timestamps, and side-by-side comparisons |
| **♻️ Quarantine Filter** | Shows only soft-deleted records |
| **Recovery Vault Modal** | Browse deleted evidence and restore with 1 click |

---

## ⚙️ Build Requirements

| Requirement | Version |
| :--- | :--- |
| **C++ Compiler** | GCC 12+ with C++17 support (Cygwin 64-bit recommended on Windows) |
| **OS** | Windows 10/11 (uses WinSock2 — `ws2_32`) |
| **Browser** | Any modern browser (Chrome, Edge, Firefox) |
| **Python** *(optional)* | Only needed to run paper generation scripts |

---

## 🔒 Evidence Integrity Design

- **SHA-256** is the primary integrity key — a single bit change produces a completely different digest.
- **MD5** is a secondary checksum only (known collision-vulnerable; never used as sole identity proof).
- **Soft-deletion** ensures binary evidence files at `storage/images/` are **never deleted** — quarantined records can always be recovered.
- **UUID-based filenames** prevent collisions and decouple physical storage from original filenames.

---

## 📄 Research Paper

A full IEEE-format research paper for this project is included:

- **[`AegisForensics_Paper.docx`](AegisForensics_Paper.docx)** — Final formatted Word document

Key results from experiments on a 120-image corpus:

| Category | Precision | Recall | F1 |
| :--- | :--- | :--- | :--- |
| Exact Duplicate | 100.0% | 100.0% | 1.000 |
| Structurally Identical | 97.4% | 95.0% | 0.962 |
| Unique Evidence | 100.0% | 100.0% | 1.000 |

---

## 👥 Authors

Developed as part of academic coursework at **Vishwakarma Institute of Technology, Pune**
Department of Engineering, Sciences and Humanities (DESH)

| Name | Role |
| :--- | :--- |
| Rutika Tilekar | System Architecture, C++ Backend, DSA Core, Frontend |
| Prathamesh Teke | Hashing Engine, Storage Layer |
| Maithili Wakde | REST API, Graph Visualization |
| Vineet Tatte | UI/UX, Testing |
| Dr. Renuka Vaidya | Faculty Guide |

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
