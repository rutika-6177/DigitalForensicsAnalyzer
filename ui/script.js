/**
 * AEGIS FORENSICS // DIGITAL EVIDENCE & DUPLICATE ANALYZER
 * Client Engine: Integrated with Flask Backend & SQLite Storage,
 * Data Structures (HashTable, Tree, Graph), Canvas Sparkles, and Audio SFX.
 */

// =========================================================
// 1. DATA STRUCTURES IMPLEMENTATIONS (CLIENT VISUAL LAYER)
// =========================================================

class ForensicHashTable {
    constructor(size = 17) {
        this.size = size;
        this.buckets = Array.from({ length: size }, () => []);
        this.count = 0;
    }

    _hash(key) {
        let hash = 0;
        for (let i = 0; i < key.length; i++) {
            hash = (hash * 31 + key.charCodeAt(i)) % this.size;
        }
        return Math.abs(hash);
    }

    insert(key, evidence) {
        const index = this._hash(key);
        const bucket = this.buckets[index];
        for (let i = 0; i < bucket.length; i++) {
            if (bucket[i].key === key) {
                bucket[i].evidence = evidence;
                return;
            }
        }
        bucket.push({ key, evidence });
        this.count++;
    }

    search(key) {
        const index = this._hash(key);
        const bucket = this.buckets[index];
        for (let i = 0; i < bucket.length; i++) {
            if (bucket[i].key === key) {
                return bucket[i].evidence;
            }
        }
        return null;
    }

    remove(key) {
        const index = this._hash(key);
        const bucket = this.buckets[index];
        for (let i = 0; i < bucket.length; i++) {
            if (bucket[i].key === key) {
                bucket.splice(i, 1);
                this.count--;
                return true;
            }
        }
        return false;
    }
}

class EvidenceTreeNode {
    constructor(id, data, parent = null) {
        this.id = id;
        this.data = data;
        this.parent = parent;
        this.children = [];
        this.depth = parent ? parent.depth + 1 : 0;
    }
}

class EvidenceTree {
    constructor() {
        this.root = new EvidenceTreeNode('ROOT', {
            name: 'Case Root: #CR-2026-AEGIS',
            type: 'CASE_ROOT',
            status: 'ORIGINAL'
        });
    }

    addEvidence(evidence, parentId = 'ROOT') {
        const parentNode = this.findNode(parentId, this.root);
        const targetParent = parentNode || this.root;
        const newNode = new EvidenceTreeNode(evidence.id, evidence, targetParent);
        targetParent.children.push(newNode);
        return newNode;
    }

    findNode(id, currentNode = this.root) {
        if (!currentNode) return null;
        if (currentNode.id === id) return currentNode;
        for (const child of currentNode.children) {
            const found = this.findNode(id, child);
            if (found) return found;
        }
        return null;
    }

    removeNode(id, currentNode = this.root) {
        for (let i = 0; i < currentNode.children.length; i++) {
            if (currentNode.children[i].id === id) {
                return currentNode.children.splice(i, 1)[0];
            }
            const found = this.removeNode(id, currentNode.children[i]);
            if (found) return found;
        }
        return null;
    }

    breadthFirst() {
        const result = [];
        const queue = [this.root];
        while (queue.length > 0) {
            const current = queue.shift();
            result.push(current);
            for (const child of current.children) {
                queue.push(child);
            }
        }
        return result;
    }

    preOrder(node = this.root, result = []) {
        if (!node) return result;
        result.push(node);
        for (const child of node.children) {
            this.preOrder(child, result);
        }
        return result;
    }

    postOrder(node = this.root, result = []) {
        if (!node) return result;
        for (const child of node.children) {
            this.postOrder(child, result);
        }
        result.push(node);
        return result;
    }
}

class EvidenceGraph {
    constructor() {
        this.adjacencyList = new Map();
    }

    addVertex(evidence) {
        if (!this.adjacencyList.has(evidence.id)) {
            this.adjacencyList.set(evidence.id, {
                vertex: evidence,
                edges: []
            });
        }
    }

    addEdge(sourceId, targetId, weight = 1.0, type = 'DUPLICATE', label = 'Match') {
        if (!this.adjacencyList.has(sourceId) || !this.adjacencyList.has(targetId)) return;

        const sourceEdges = this.adjacencyList.get(sourceId).edges;
        if (!sourceEdges.some(e => e.targetId === targetId)) {
            sourceEdges.push({ targetId, weight, type, label });
        }

        const targetEdges = this.adjacencyList.get(targetId).edges;
        if (!targetEdges.some(e => e.targetId === sourceId)) {
            targetEdges.push({ targetId: sourceId, weight, type, label });
        }
    }

    removeVertex(id) {
        this.adjacencyList.delete(id);
        for (const entry of this.adjacencyList.values()) {
            entry.edges = entry.edges.filter(e => e.targetId !== id);
        }
    }

    getTotalEdges() {
        let total = 0;
        for (const entry of this.adjacencyList.values()) {
            total += entry.edges.length;
        }
        return Math.floor(total / 2);
    }

    bfs(startId) {
        const visited = new Set();
        const traversalOrder = [];
        const queue = [startId];
        visited.add(startId);

        while (queue.length > 0) {
            const currentId = queue.shift();
            traversalOrder.push(currentId);
            const entry = this.adjacencyList.get(currentId);
            if (entry) {
                for (const edge of entry.edges) {
                    if (!visited.has(edge.targetId)) {
                        visited.add(edge.targetId);
                        queue.push(edge.targetId);
                    }
                }
            }
        }
        return traversalOrder;
    }
}

// =========================================================
// 2. CURSOR SPARKLE PARTICLE SYSTEM
// =========================================================

class SparkleEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.enabled = true;
        this.colors = ['#00f0ff', '#00ff9d', '#bd00ff', '#ffb700', '#ffffff'];

        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.bindEvents();
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    bindEvents() {
        window.addEventListener('mousemove', (e) => {
            if (!this.enabled) return;
            for (let i = 0; i < 3; i++) {
                this.addParticle(e.clientX, e.clientY);
            }
        });

        window.addEventListener('click', (e) => {
            if (!this.enabled) return;
            for (let i = 0; i < 28; i++) {
                this.addParticle(e.clientX, e.clientY, true);
            }
        });
    }

    addParticle(x, y, isExplosion = false) {
        const angle = Math.random() * Math.PI * 2;
        const speed = isExplosion ? (Math.random() * 4.5 + 2) : (Math.random() * 2 + 0.5);
        const size = isExplosion ? (Math.random() * 5 + 3) : (Math.random() * 4 + 2);

        this.particles.push({
            x,
            y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed + (isExplosion ? -1 : 0.2),
            size,
            alpha: 1.0,
            decay: isExplosion ? (Math.random() * 0.02 + 0.015) : (Math.random() * 0.025 + 0.02),
            color: this.colors[Math.floor(Math.random() * this.colors.length)],
            rotation: Math.random() * Math.PI * 2,
            rotSpeed: (Math.random() - 0.5) * 0.1,
            shape: Math.random() > 0.4 ? 'star' : 'circle'
        });

        if (this.particles.length > 250) {
            this.particles.shift();
        }
    }

    drawStar(ctx, x, y, size, rotation) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(rotation);
        ctx.beginPath();
        const spikes = 4;
        const step = Math.PI / spikes;
        let rot = Math.PI / 2 * 3;
        ctx.moveTo(0, -size);
        for (let i = 0; i < spikes; i++) {
            ctx.lineTo(Math.cos(rot) * size, Math.sin(rot) * size);
            rot += step;
            ctx.lineTo(Math.cos(rot) * (size * 0.28), Math.sin(rot) * (size * 0.28));
            rot += step;
        }
        ctx.lineTo(0, -size);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.04;
            p.alpha -= p.decay;
            p.rotation += p.rotSpeed;
            p.size *= 0.985;

            if (p.alpha <= 0 || p.size <= 0.5) {
                this.particles.splice(i, 1);
                continue;
            }

            this.ctx.save();
            this.ctx.globalAlpha = Math.max(0, p.alpha);
            this.ctx.fillStyle = p.color;
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = p.color;

            if (p.shape === 'star') {
                this.drawStar(this.ctx, p.x, p.y, p.size, p.rotation);
            } else {
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.size / 2, 0, Math.PI * 2);
                this.ctx.fill();
            }
            this.ctx.restore();
        }
    }
}

// =========================================================
// 3. AUDIO SYNTHESIZER (WEB AUDIO API)
// =========================================================

class CyberAudio {
    constructor() {
        this.ctx = null;
        this.enabled = true;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
    }

    play(freq, type = 'sine', duration = 0.1, gainVal = 0.08) {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
            gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + duration);
        } catch (e) {}
    }

    playSuccess() {
        setTimeout(() => this.play(523.25, 'sine', 0.12, 0.08), 0);
        setTimeout(() => this.play(659.25, 'sine', 0.12, 0.08), 80);
        setTimeout(() => this.play(783.99, 'sine', 0.25, 0.1), 160);
    }

    playAlert() {
        setTimeout(() => this.play(440, 'triangle', 0.1, 0.1), 0);
        setTimeout(() => this.play(349.23, 'triangle', 0.2, 0.1), 100);
    }

    playBlip() {
        this.play(880, 'sine', 0.04, 0.05);
    }

    playScan() {
        this.init();
        if (!this.ctx || !this.enabled) return;
        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(200, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(1400, this.ctx.currentTime + 0.25);
            gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.25);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.25);
        } catch (e) {}
    }
}

// =========================================================
// 4. GLOBAL STATE & RECORD FORMATTING
// =========================================================

const forensicDB = {
    evidenceList: [],
    hashTable: new ForensicHashTable(17),
    tree: new EvidenceTree(),
    graph: new EvidenceGraph()
};

const audio = new CyberAudio();
let sparkler = null;
let currentVaultFilter = 'all';
let selectedFilesQueue = [];

function formatBytes(bytes, decimals = 2) {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatBackendRecord(item) {
    const isDup = item.status === 'DUPLICATE';
    const storagePath = item.storage_path || item.storagePath || '';
    const storageFilename = storagePath ? storagePath.split(/[/\\]/).pop() : (item.file_name || item.fileName);
    const thumbUrl = storageFilename ? `/storage/images/${storageFilename}` : (item.dataUrl || '');

    return {
        id: item.id,
        fileName: item.file_name || item.fileName || 'unknown.jpg',
        fileSize: item.file_size !== undefined ? item.file_size : (item.fileSize || 0),
        fileSizeFormatted: formatBytes(item.file_size !== undefined ? item.file_size : (item.fileSize || 0)),
        mimeType: item.mime_type || item.mimeType || 'image/jpeg',
        dimensions: item.dimensions || '800 × 600 px',
        aspectRatio: item.aspect_ratio || item.aspectRatio || '4:3',
        sha256: item.sha256 || '',
        md5: item.md5 || '',
        dHashHex: item.dhash_hex || item.dHashHex || '',
        dHashBinary: item.dhash_bin || item.dHashBinary || '',
        status: item.status || 'ORIGINAL',
        matchType: item.match_type || item.matchType || (isDup ? 'EXACT_HASH' : 'NONE'),
        matchedParentId: item.matched_parent_id || item.matchedParentId || null,
        similarityScore: item.similarity_score !== undefined ? item.similarity_score : (item.similarityScore || 100),
        storagePath: storagePath,
        storageFilename: storageFilename,
        isPhysicalCopy: item.is_physical_copy !== undefined ? item.is_physical_copy : (item.isPhysicalCopy !== undefined ? item.isPhysicalCopy : 1),
        timestamp: item.timestamp || new Date().toISOString(),
        timestampFormatted: item.timestamp ? new Date(item.timestamp).toLocaleString() : new Date().toLocaleString(),
        device: item.device || 'Forensic Station',
        custodyStatus: item.custody_status || item.custodyStatus || 'Verified & Logged',
        dataUrl: thumbUrl
    };
}

function syncStateFromBackend(summaryData) {
    forensicDB.evidenceList = [];
    forensicDB.hashTable = new ForensicHashTable(17);
    forensicDB.tree = new EvidenceTree();
    forensicDB.graph = new EvidenceGraph();

    const rawList = summaryData.evidence_list || [];
    for (const raw of rawList) {
        const item = formatBackendRecord(raw);
        forensicDB.evidenceList.push(item);
        forensicDB.hashTable.insert(item.sha256, item);

        if (item.status === 'ORIGINAL' || !item.matchedParentId) {
            forensicDB.tree.addEvidence(item, 'ROOT');
            forensicDB.graph.addVertex(item);
        } else {
            forensicDB.tree.addEvidence(item, item.matchedParentId);
            forensicDB.graph.addVertex(item);
            const weight = item.matchType === 'EXACT_HASH' ? 1.0 : (item.similarityScore / 100.0);
            forensicDB.graph.addEdge(item.matchedParentId, item.id, weight, item.matchType);
        }
    }

    updateDashboardKPIs();
    renderQuickEvidenceList();
    renderTreeSvg();
    drawGraph();
    renderVaultTable();
    renderDSALab();
}

// =========================================================
// 5. INITIALIZATION & BACKEND PERSISTENCE FETCH
// =========================================================

document.addEventListener('DOMContentLoaded', () => {
    sparkler = new SparkleEngine('sparkleCanvas');
    setupDropZone();

    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    initGraphCanvas();
    loadEvidenceFromBackend();
});

async function loadEvidenceFromBackend() {
    try {
        const res = await fetch('/api/evidence');
        if (!res.ok) throw new Error('API request failed');
        const data = await res.json();
        if (data && data.evidence_list) {
            syncStateFromBackend(data);
            showToast(`Loaded ${data.evidence_list.length} evidence records from SQLite database`, 'info');
        }
    } catch (err) {
        console.warn('Backend not available, running in client memory mode:', err);
        updateDashboardKPIs();
        renderQuickEvidenceList();
        renderTreeSvg();
        renderVaultTable();
        renderDSALab();
    }
}

function switchPage(pageId) {
    audio.playBlip();
    document.querySelectorAll('.nav-tab').forEach(tab => {
        const isActive = tab.getAttribute('data-page') === pageId;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('.page-view').forEach(p => {
        p.classList.toggle('active-view', p.id === `page-${pageId}`);
    });

    if (pageId === 'vault') {
        renderVaultTable();
    } else if (pageId === 'dsa') {
        renderDSALab();
    } else if (pageId === 'analyzer') {
        renderTreeSvg();
        drawGraph();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleSparkles() {
    if (!sparkler) return;
    sparkler.enabled = !sparkler.enabled;
    const statusText = document.getElementById('sparkleStatusText');
    if (statusText) statusText.textContent = sparkler.enabled ? 'ON' : 'OFF';
    showToast(sparkler.enabled ? '✨ Cursor Sparkles Activated' : '✨ Cursor Sparkles Paused', 'info');
}

function toggleAudio() {
    audio.enabled = !audio.enabled;
    const soundText = document.getElementById('soundStatusText');
    const soundIcon = document.getElementById('soundIcon');
    if (soundText) soundText.textContent = audio.enabled ? 'ON' : 'OFF';
    if (soundIcon) soundIcon.textContent = audio.enabled ? '🔊' : '🔇';
    if (audio.enabled) audio.playSuccess();
    showToast(audio.enabled ? '🔊 Cyber Audio ON' : '🔇 Cyber Audio Muted', 'info');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('cyberToast');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast-msg ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '⚡' : type === 'alert' ? '⚠️' : 'ℹ️'}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, 4000);
}

// =========================================================
// 6. UPLOAD HANDLING & DEDUPLICATION (FLASK + SQLITE)
// =========================================================

function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (files.length > 0) {
            handleFiles(files);
        } else {
            showToast('Please drop image files (JPG, PNG, WEBP, GIF)', 'alert');
        }
    });

    dropZone.addEventListener('click', (e) => {
        if (e.target.id !== 'browseButton' && !e.target.closest('#browseButton')) {
            document.getElementById('fileInput').click();
        }
    });
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files).filter(f => f.type.startsWith('image/'));
    if (files.length > 0) {
        handleFiles(files);
    }
}

function handleFiles(files) {
    selectedFilesQueue = files;
    const selectedBadge = document.getElementById('selectedFile');
    if (selectedBadge) {
        selectedBadge.hidden = false;
        selectedBadge.innerHTML = `📁 ${files.length} file(s) staged: <strong>${files.map(f => f.name).join(', ')}</strong>`;
    }
    audio.playBlip();
    showToast(`${files.length} image(s) ready for analysis`, 'info');
}

async function uploadEvidence() {
    if (!selectedFilesQueue || selectedFilesQueue.length === 0) {
        showToast('Please select or drop at least one image first', 'alert');
        return;
    }

    const uploadBtn = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = `
        <svg viewBox="0 0 24 24" class="spin"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="30 10"/></svg>
        <span>Running Forensic Pipeline...</span>
    `;
    audio.playScan();

    try {
        const formData = new FormData();
        for (const file of selectedFilesQueue) {
            formData.append('files', file);
        }

        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            if (data.summary) {
                syncStateFromBackend(data.summary);
            }
            if (data.processed && data.processed.length > 0) {
                const last = formatBackendRecord(data.processed[data.processed.length - 1]);
                displayAnalysisResult(last);
                if (last.status === 'DUPLICATE') {
                    audio.playAlert();
                    showToast(`Duplicate Detected! Linked to [${last.matchedParentId}]. 0 duplicate copies stored.`, 'alert');
                } else {
                    audio.playSuccess();
                    showToast(`Original evidence stored in storage/images/: ${last.id}`, 'success');
                }
            }

            uploadStatus.innerHTML = `
                <div class="msg success">
                    ✓ Persisted to SQLite database and storage/images/ with deduplication.
                </div>
            `;
            setTimeout(() => { uploadStatus.innerHTML = ''; }, 4500);
        } else {
            throw new Error('Upload API returned error status');
        }
    } catch (err) {
        console.error('Upload error:', err);
        uploadStatus.innerHTML = `<div class="msg error">Upload failed: ${err.message}</div>`;
        audio.playAlert();
    } finally {
        selectedFilesQueue = [];
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';
        const selectedBadge = document.getElementById('selectedFile');
        if (selectedBadge) selectedBadge.hidden = true;

        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `
            <svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>Analyze Image Evidence Now</span>
        `;
    }
}

async function loadSampleDataset() {
    showToast('Loading pre-compiled Forensic Dataset...', 'info');
    audio.playScan();

    try {
        const res = await fetch('/api/sample', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            if (data.summary) {
                syncStateFromBackend(data.summary);
            }
            if (data.processed && data.processed.length > 0) {
                displayAnalysisResult(formatBackendRecord(data.processed[data.processed.length - 1]));
            }
            showToast('Sample dataset loaded & stored in database and storage/images/!', 'success');
            audio.playSuccess();
        }
    } catch (err) {
        console.error('Failed to load sample dataset:', err);
    }
}

async function deleteEvidence(id) {
    if (!confirm(`Are you sure you want to remove evidence [${id}] from the database?`)) return;

    try {
        const res = await fetch(`/api/evidence/${id}`, { method: 'DELETE' });
        if (res.ok) {
            const data = await res.json();
            if (data.summary) {
                syncStateFromBackend(data.summary);
            }
            audio.playAlert();
            showToast(`Evidence ${id} purged from SQLite database`, 'alert');
        }
    } catch (err) {
        console.error('Delete error:', err);
    }
}

async function clearAllEvidence() {
    if (!confirm('⚠️ WARNING: Are you sure you want to permanently delete ALL evidence records and all physical stored images? This action cannot be undone.')) {
        return;
    }

    try {
        const res = await fetch('/api/clear', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            if (data.summary) {
                syncStateFromBackend(data.summary);
            }
            audio.playAlert();
            showToast('All evidence and storage images have been purged', 'alert');
        }
    } catch (err) {
        console.error('Clear error:', err);
    }
}

// =========================================================
// 7. COUNTERS & VERDICT HERO CARD
// =========================================================

function updateDashboardKPIs() {
    const total = forensicDB.evidenceList.length;
    const originals = forensicDB.evidenceList.filter(e => e.status === 'ORIGINAL').length;
    const duplicates = forensicDB.evidenceList.filter(e => e.status === 'DUPLICATE').length;
    const exactDups = forensicDB.evidenceList.filter(e => e.matchType === 'EXACT_HASH').length;
    const nearDups = forensicDB.evidenceList.filter(e => e.matchType === 'PERCEPTUAL_DHASH').length;
    const totalEdges = forensicDB.graph.getTotalEdges();

    animateCounter('totalEvidence', total);
    animateCounter('originalEvidence', originals);
    animateCounter('duplicateEvidence', duplicates);
    animateCounter('relationships', totalEdges);

    const exactElem = document.getElementById('exactDupCount');
    if (exactElem) exactElem.textContent = exactDups;
    const nearElem = document.getElementById('nearDupCount');
    if (nearElem) nearElem.textContent = nearDups;

    const badge = document.getElementById('vaultCountBadge');
    if (badge) badge.textContent = total;

    const vTotal = document.getElementById('vaultTotalRecords');
    if (vTotal) vTotal.textContent = total;
    const vOrig = document.getElementById('vaultOriginalsCount');
    if (vOrig) vOrig.textContent = originals;
    const vDup = document.getElementById('vaultDuplicatesCount');
    if (vDup) vDup.textContent = duplicates;

    const totalBytes = forensicDB.evidenceList.reduce((sum, e) => sum + (e.fileSize || 0), 0);
    const vSize = document.getElementById('vaultStorageSize');
    if (vSize) vSize.textContent = formatBytes(totalBytes);

    const fAll = document.getElementById('filterAllCount');
    if (fAll) fAll.textContent = total;
    const fOrig = document.getElementById('filterOriginalCount');
    if (fOrig) fOrig.textContent = originals;
    const fDup = document.getElementById('filterDuplicateCount');
    if (fDup) fDup.textContent = duplicates;
}

function animateCounter(id, targetValue) {
    const elem = document.getElementById(id);
    if (!elem) return;
    const startValue = parseInt(elem.textContent) || 0;
    if (startValue === targetValue) {
        elem.textContent = targetValue;
        return;
    }

    const duration = 350;
    const startTime = performance.now();

    function updateNumber(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(startValue + (targetValue - startValue) * progress);
        elem.textContent = current;
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        } else {
            elem.textContent = targetValue;
        }
    }
    requestAnimationFrame(updateNumber);
}

function displayAnalysisResult(evidence) {
    const resultPanel = document.getElementById('resultPanel');
    const resultContainer = document.getElementById('result');
    if (!resultPanel || !resultContainer) return;

    resultPanel.hidden = false;

    const isDup = evidence.status === 'DUPLICATE';
    const statusClass = isDup ? 'duplicate' : 'original';
    const statusLabel = isDup
        ? `DUPLICATE DETECTED (${evidence.similarityScore}% Match)`
        : 'ORIGINAL EVIDENCE VERIFIED';

    let verdictDesc = '';
    if (isDup) {
        verdictDesc = evidence.matchType === 'EXACT_HASH'
            ? `Exact cryptographic duplicate of <strong>[${evidence.matchedParentId}]</strong>. Deduplication active: 0 redundant physical copies written.`
            : `Perceptual visual duplicate of <strong>[${evidence.matchedParentId}]</strong> (${evidence.similarityScore}% dHash match). Linked to parent root.`;
    } else {
        verdictDesc = `Unique cryptographic root. Stored as distinct physical copy at <code>${evidence.storagePath}</code>.`;
    }

    resultContainer.innerHTML = `
        <div class="analysis-summary">
            <div class="analysis-hero">
                <div class="verdict-header">
                    <span class="analysis-status ${statusClass}">
                        ${isDup ? '⚠️' : '✓'} ${statusLabel}
                    </span>
                    <button class="secondary-button" onclick="inspectEvidenceModal('${evidence.id}')">
                        Inspect Full Dossier
                    </button>
                </div>

                <h3 class="analysis-title">${escapeHtml(evidence.fileName)}</h3>
                <p class="analysis-subtitle">${verdictDesc}</p>

                <div class="analysis-preview-row">
                    <img src="${evidence.dataUrl}" alt="Preview" class="analysis-thumb">
                    <div>
                        <div class="evidence-id-badge">${evidence.id}</div>
                        <div style="margin-top: 4px; font-size: 11px; color: var(--text-secondary);">
                            ${evidence.dimensions} • ${evidence.fileSizeFormatted}
                        </div>
                        <div style="margin-top: 3px; font-size: 10px; color: var(--neon-cyan);">
                            Storage: ${evidence.isPhysicalCopy === 1 ? '💾 Unique File' : '🔗 Reused / Deduplicated'}
                        </div>
                    </div>
                    ${isDup && evidence.matchedParentId ? `
                        <div style="margin-left: auto; text-align: right;">
                            <span style="font-size: 10px; color: var(--neon-amber); font-weight: 700;">PARENT ORIGINAL:</span>
                            <div class="evidence-id-badge" style="border-color: var(--neon-amber); color: var(--neon-amber); cursor: pointer;" onclick="inspectEvidenceModal('${evidence.matchedParentId}')">
                                ${evidence.matchedParentId}
                            </div>
                        </div>
                    ` : ''}
                </div>

                <div class="analysis-meta">
                    <div class="analysis-mini">
                        <span>DATA STRUCTURE ACTION</span>
                        <strong>${isDup ? `Tree: Child leaf under ${evidence.matchedParentId}` : 'Tree: Root branch node'}</strong>
                    </div>
                    <div class="analysis-mini">
                        <span>PERSISTENCE</span>
                        <strong>SQLite (database/forensic.db)</strong>
                    </div>
                </div>
            </div>

            <div class="hash-block">
                <h3>
                    <span>CRYPTOGRAPHIC FINGERPRINTS</span>
                    <span style="font-size: 10px; color: var(--neon-green);">SHA-256 + MD5 + dHash</span>
                </h3>

                <div class="hash-row">
                    <span>SHA-256 HASH</span>
                    <div class="hash-value-wrap">
                        <span class="hash-value">${evidence.sha256}</span>
                        <button class="copy-btn" onclick="copyText('${evidence.sha256}')">Copy</button>
                    </div>
                </div>

                <div class="hash-row">
                    <span>MD5 HASH</span>
                    <div class="hash-value-wrap">
                        <span class="hash-value">${evidence.md5}</span>
                        <button class="copy-btn" onclick="copyText('${evidence.md5}')">Copy</button>
                    </div>
                </div>

                <div class="hash-row">
                    <span>PERCEPTUAL dHASH (64-bit Hex)</span>
                    <div class="hash-value-wrap">
                        <span class="hash-value">${evidence.dHashHex}</span>
                        <button class="copy-btn" onclick="copyText('${evidence.dHashHex}')">Copy</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        audio.playBlip();
        showToast('Hash copied to clipboard', 'info');
    });
}

// =========================================================
// 8. QUICK REPOSITORY PREVIEW TABLE
// =========================================================

function renderQuickEvidenceList() {
    const container = document.getElementById('quickEvidenceList');
    if (!container) return;

    if (forensicDB.evidenceList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📁</div>
                <strong>Evidence Repository Empty</strong>
                <p>Upload image evidence or click "Load Sample Forensic Evidence" above.</p>
            </div>
        `;
        return;
    }

    const recent = [...forensicDB.evidenceList].reverse().slice(0, 5);

    let html = `
        <table class="repository-table">
            <thead>
                <tr>
                    <th>Evidence ID</th>
                    <th>File Details</th>
                    <th>Status</th>
                    <th>Parent / Original</th>
                    <th>Storage Reference</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const item of recent) {
        const isDup = item.status === 'DUPLICATE';
        const parentDisplay = isDup && item.matchedParentId
            ? `<span class="evidence-id-badge" style="border-color: var(--neon-amber); color: var(--neon-amber); cursor: pointer;" onclick="inspectEvidenceModal('${item.matchedParentId}')">${item.matchedParentId}</span>`
            : `<span style="color: var(--text-muted); font-size: 11px;">ROOT (Original)</span>`;

        const storagePill = item.isPhysicalCopy === 1
            ? `<span class="storage-pill unique" title="Physical file in storage/images/">💾 Unique File</span>`
            : `<span class="storage-pill shared" title="Deduplicated: shares physical storage with original">🔗 Shared [${item.matchedParentId}]</span>`;

        html += `
            <tr>
                <td><span class="evidence-id-badge">${item.id}</span></td>
                <td>
                    <div class="file-cell">
                        <img src="${item.dataUrl}" class="file-thumb" onclick="inspectEvidenceModal('${item.id}')" title="Click to inspect">
                        <div>
                            <div class="file-name">${escapeHtml(item.fileName)}</div>
                            <div class="file-sub">${item.fileSizeFormatted} • ${item.dimensions}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="status-badge ${isDup ? 'duplicate' : 'original'}">
                        ${isDup ? `Duplicate (${item.similarityScore}%)` : 'Original'}
                    </span>
                </td>
                <td>${parentDisplay}</td>
                <td>${storagePill}</td>
                <td>
                    <button class="secondary-button" style="padding: 5px 12px; font-size: 11px;" onclick="inspectEvidenceModal('${item.id}')">
                        Inspect
                    </button>
                </td>
            </tr>
        `;
    }

    html += `</tbody></table>`;
    container.innerHTML = html;
}

// =========================================================
// 9. DEDICATED EVIDENCE VAULT TABLE (WITH STORAGE & PARENT ID)
// =========================================================

function filterVaultData() {
    renderVaultTable();
}

function setVaultFilter(filter) {
    currentVaultFilter = filter;
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-filter') === filter);
    });
    renderVaultTable();
}

function clearVaultSearch() {
    const searchInput = document.getElementById('vaultSearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    if (searchInput) searchInput.value = '';
    if (clearBtn) clearBtn.hidden = true;
    renderVaultTable();
}

function renderVaultTable() {
    const tbody = document.getElementById('vaultTableBody');
    const emptyState = document.getElementById('vaultEmptyState');
    const searchInput = document.getElementById('vaultSearchInput');
    const sortSelect = document.getElementById('vaultSort');
    const clearBtn = document.getElementById('clearSearchBtn');

    if (!tbody) return;

    const searchTerm = (searchInput ? searchInput.value : '').toLowerCase().trim();
    if (clearBtn) clearBtn.hidden = !searchTerm;

    let items = [...forensicDB.evidenceList];

    if (currentVaultFilter === 'original') {
        items = items.filter(i => i.status === 'ORIGINAL');
    } else if (currentVaultFilter === 'duplicate') {
        items = items.filter(i => i.status === 'DUPLICATE');
    }

    if (searchTerm) {
        items = items.filter(i =>
            i.id.toLowerCase().includes(searchTerm) ||
            i.fileName.toLowerCase().includes(searchTerm) ||
            i.sha256.toLowerCase().includes(searchTerm) ||
            i.md5.toLowerCase().includes(searchTerm) ||
            i.dHashHex.toLowerCase().includes(searchTerm) ||
            (i.matchedParentId && i.matchedParentId.toLowerCase().includes(searchTerm))
        );
    }

    const sortMode = sortSelect ? sortSelect.value : 'date-desc';
    items.sort((a, b) => {
        if (sortMode === 'date-desc') return new Date(b.timestamp) - new Date(a.timestamp);
        if (sortMode === 'date-asc') return new Date(a.timestamp) - new Date(b.timestamp);
        if (sortMode === 'size-desc') return b.fileSize - a.fileSize;
        if (sortMode === 'size-asc') return a.fileSize - b.fileSize;
        if (sortMode === 'name-asc') return a.fileName.localeCompare(b.fileName);
        return 0;
    });

    if (items.length === 0) {
        tbody.innerHTML = '';
        if (emptyState) emptyState.hidden = false;
        return;
    }

    if (emptyState) emptyState.hidden = true;

    tbody.innerHTML = items.map(item => {
        const isDup = item.status === 'DUPLICATE';

        const parentDisplay = isDup && item.matchedParentId
            ? `<div class="evidence-id-badge" style="border-color: var(--neon-amber); color: var(--neon-amber); cursor: pointer;" onclick="inspectEvidenceModal('${item.matchedParentId}')" title="Click to inspect parent">${item.matchedParentId}</div>`
            : `<span style="color: var(--text-muted); font-size: 11px;">ROOT (Original)</span>`;

        const filenameOnDisk = item.storagePath ? item.storagePath.split(/[/\\]/).pop() : item.fileName;
        const storageDisplay = item.isPhysicalCopy === 1
            ? `<span class="storage-pill unique" title="Physical file in storage/images/${filenameOnDisk}">💾 Unique (${filenameOnDisk})</span>`
            : `<span class="storage-pill shared" title="Deduplicated: shares physical storage with ${item.matchedParentId}">🔗 Reused [${item.matchedParentId}] (0 bytes added)</span>`;

        return `
            <tr>
                <td><span class="evidence-id-badge">${item.id}</span></td>
                <td>
                    <img src="${item.dataUrl}" class="file-thumb" onclick="inspectEvidenceModal('${item.id}')" title="Click to enlarge" style="width: 50px; height: 50px;">
                </td>
                <td>
                    <div class="file-name">${escapeHtml(item.fileName)}</div>
                    <span class="file-sub">${item.mimeType}</span>
                </td>
                <td>
                    <strong style="color: var(--neon-cyan);">${item.fileSizeFormatted}</strong>
                    <div style="font-size: 10px; color: var(--text-muted);">${item.fileSize.toLocaleString()} bytes</div>
                </td>
                <td>
                    <div>${item.dimensions}</div>
                    <div style="font-size: 10px; color: var(--text-muted);">${item.aspectRatio}</div>
                </td>
                <td>
                    <span class="status-badge ${isDup ? 'duplicate' : 'original'}">
                        ${isDup ? `Duplicate (${item.similarityScore}%)` : 'Original'}
                    </span>
                </td>
                <td>${parentDisplay}</td>
                <td>${storageDisplay}</td>
                <td>
                    <div class="hash-cell">
                        <span class="hash-truncated" title="${item.sha256}">${item.sha256}</span>
                        <button class="copy-btn" onclick="copyText('${item.sha256}')" title="Copy SHA-256">📋</button>
                    </div>
                </td>
                <td>
                    <div class="hash-cell">
                        <span class="hash-truncated" title="${item.md5}">${item.md5}</span>
                        <button class="copy-btn" onclick="copyText('${item.md5}')" title="Copy MD5">📋</button>
                    </div>
                </td>
                <td>
                    <div class="hash-cell">
                        <span class="hash-truncated" title="${item.dHashHex}">${item.dHashHex}</span>
                        <button class="copy-btn" onclick="copyText('${item.dHashHex}')" title="Copy dHash">📋</button>
                    </div>
                </td>
                <td>
                    <div style="font-size: 11px; color: var(--text-secondary);">${item.timestampFormatted}</div>
                </td>
                <td>
                    <div class="table-actions-cell">
                        <button class="row-action-btn" onclick="inspectEvidenceModal('${item.id}')" title="View Full Dossier">Dossier</button>
                        <button class="row-action-btn delete-btn" onclick="deleteEvidence('${item.id}')" title="Delete from case">✕</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function exportEvidenceJSON() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(forensicDB.evidenceList, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `forensic_evidence_dossier_${Date.now()}.json`);
    dlAnchor.click();
    showToast('Evidence JSON Dossier Exported', 'success');
}

function exportEvidenceCSV() {
    if (forensicDB.evidenceList.length === 0) {
        showToast('No evidence records to export', 'alert');
        return;
    }

    const headers = ['EvidenceID', 'FileName', 'FileSize_Bytes', 'MIMEType', 'Dimensions', 'Status', 'ParentID', 'StorageReference', 'SHA256', 'MD5', 'dHashHex', 'Timestamp'];
    const rows = forensicDB.evidenceList.map(e => [
        e.id,
        `"${e.fileName.replace(/"/g, '""')}"`,
        e.fileSize,
        e.mimeType,
        `"${e.dimensions}"`,
        e.status,
        e.matchedParentId || 'ROOT',
        e.isPhysicalCopy === 1 ? 'Unique_File' : `Shared_With_${e.matchedParentId}`,
        e.sha256,
        e.md5,
        e.dHashHex,
        `"${e.timestamp}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", encodeURI(csvContent));
    dlAnchor.setAttribute("download", `forensic_evidence_ledger_${Date.now()}.csv`);
    dlAnchor.click();
    showToast('Evidence CSV Ledger Exported', 'success');
}

// =========================================================
// 10. TREE DATA STRUCTURE VISUALIZATION
// =========================================================

function renderTreeSvg() {
    const svg = document.getElementById('treeSvg');
    if (!svg) return;

    svg.innerHTML = '';
    const root = forensicDB.tree.root;

    if (!root || (root.children.length === 0 && forensicDB.evidenceList.length === 0)) {
        svg.innerHTML = `
            <text x="50%" y="50%" text-anchor="middle" fill="#5e7394" font-family="Rajdhani" font-size="14">
                Evidence Tree Empty. Upload images to construct the hierarchy.
            </text>
        `;
        return;
    }

    const levelHeight = 90;
    const nodeRadius = 24;
    const nodes = [];
    const links = [];

    function assignPositions(node, xStart, xEnd, depth) {
        const x = (xStart + xEnd) / 2;
        const y = depth * levelHeight + 50;
        nodes.push({ node, x, y });

        const children = node.children || [];
        if (children.length > 0) {
            const step = (xEnd - xStart) / children.length;
            for (let i = 0; i < children.length; i++) {
                const childXStart = xStart + i * step;
                const childXEnd = childXStart + step;
                links.push({
                    sourceNode: node,
                    targetNode: children[i],
                    x1: x,
                    y1: y,
                    x2: (childXStart + childXEnd) / 2,
                    y2: (depth + 1) * levelHeight + 50
                });
                assignPositions(children[i], childXStart, childXEnd, depth + 1);
            }
        }
    }

    const svgWidth = Math.max(svg.clientWidth || 650, (root.children.length * 140) + 100);
    svg.setAttribute('width', svgWidth);
    svg.setAttribute('height', Math.max(480, (getMaxTreeDepth(root) + 1) * levelHeight + 80));

    assignPositions(root, 20, svgWidth - 20, 0);

    for (const link of links) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const midY = (link.y1 + link.y2) / 2;
        const d = `M ${link.x1} ${link.y1} C ${link.x1} ${midY}, ${link.x2} ${midY}, ${link.x2} ${link.y2}`;
        path.setAttribute('d', d);
        path.setAttribute('class', 'tree-link');
        svg.appendChild(path);
    }

    for (const item of nodes) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'tree-node-group');
        g.setAttribute('id', `treenode-${item.node.id}`);
        g.setAttribute('transform', `translate(${item.x}, ${item.y})`);

        const isRoot = item.node.id === 'ROOT';
        const isDup = item.node.data.status === 'DUPLICATE';

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', isRoot ? 24 : nodeRadius);
        circle.setAttribute('class', 'tree-node-circle');
        circle.setAttribute('fill', isRoot ? '#172554' : isDup ? '#2a1a08' : '#042f2e');
        circle.setAttribute('stroke', isRoot ? '#3b82f6' : isDup ? '#ffb700' : '#00ff9d');
        circle.setAttribute('stroke-width', '2');
        g.appendChild(circle);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('y', 4);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('class', 'tree-node-text');
        text.textContent = isRoot ? 'ROOT' : item.node.id;
        g.appendChild(text);

        const subtext = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        subtext.setAttribute('y', 36);
        subtext.setAttribute('text-anchor', 'middle');
        subtext.setAttribute('class', 'tree-node-subtext');
        subtext.textContent = isRoot ? 'Case Root' : isDup ? `Dup (${item.node.data.similarityScore}%)` : 'Original';
        g.appendChild(subtext);

        if (!isRoot) {
            g.addEventListener('click', () => {
                inspectEvidenceModal(item.node.id);
            });
        }

        svg.appendChild(g);
    }
}

function getMaxTreeDepth(node) {
    if (!node || node.children.length === 0) return 0;
    let max = 0;
    for (const child of node.children) {
        max = Math.max(max, getMaxTreeDepth(child));
    }
    return 1 + max;
}

function expandAllTreeNodes() {
    renderTreeSvg();
    audio.playBlip();
    showToast('Tree hierarchy refreshed', 'info');
}

async function animateTreeTraversal(type) {
    let order = [];
    let traversalName = '';

    if (type === 'bfs') {
        traversalName = 'Breadth-First (Level-Order) Traversal';
        order = forensicDB.tree.breadthFirst();
    } else if (type === 'preorder') {
        traversalName = 'Pre-Order Traversal [Root -> Children]';
        order = forensicDB.tree.preOrder();
    } else if (type === 'postorder') {
        traversalName = 'Post-Order Traversal [Children -> Root]';
        order = forensicDB.tree.postOrder();
    }

    const logBox = document.getElementById('treeLog');
    const logContent = document.getElementById('treeLogContent');
    if (logBox) logBox.hidden = false;
    if (logContent) {
        logContent.innerHTML = `<strong>[TRAVERSING] ${traversalName}</strong><br>Visiting sequence: `;
    }

    document.querySelectorAll('.tree-node-circle').forEach(c => {
        c.setAttribute('filter', 'none');
    });

    for (let i = 0; i < order.length; i++) {
        const node = order[i];
        const g = document.getElementById(`treenode-${node.id}`);
        if (g) {
            const circle = g.querySelector('.tree-node-circle');
            if (circle) {
                circle.setAttribute('fill', '#00f0ff');
                circle.setAttribute('stroke', '#ffffff');
                circle.setAttribute('filter', 'drop-shadow(0 0 12px #00f0ff)');
            }
        }

        audio.play(400 + i * 40, 'sine', 0.08, 0.06);

        if (logContent) {
            logContent.innerHTML += ` <span style="color:#fff; font-weight:bold;">[${node.id}]</span> →`;
        }

        await new Promise(r => setTimeout(r, 380));

        if (g) {
            const circle = g.querySelector('.tree-node-circle');
            if (circle) {
                const isRoot = node.id === 'ROOT';
                const isDup = node.data.status === 'DUPLICATE';
                circle.setAttribute('fill', isRoot ? '#172554' : isDup ? '#2a1a08' : '#042f2e');
                circle.setAttribute('stroke', isRoot ? '#3b82f6' : isDup ? '#ffb700' : '#00ff9d');
                circle.setAttribute('filter', 'none');
            }
        }
    }

    if (logContent) {
        logContent.innerHTML += ` <span style="color:var(--neon-green); font-weight:bold;">COMPLETE (${order.length} nodes)</span>`;
    }
    audio.playSuccess();
}

// =========================================================
// 11. GRAPH DATA STRUCTURE (FORCE-DIRECTED PHYSICS)
// =========================================================

let graphNodes = [];
let graphEdges = [];
let graphCanvas = null;
let graphCtx = null;
let draggedNode = null;
let hoveredNode = null;

function initGraphCanvas() {
    graphCanvas = document.getElementById('graphCanvas');
    if (!graphCanvas) return;
    graphCtx = graphCanvas.getContext('2d');

    function resizeCanvas() {
        const rect = graphCanvas.parentElement.getBoundingClientRect();
        graphCanvas.width = rect.width;
        graphCanvas.height = rect.height || 520;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    graphCanvas.addEventListener('mousedown', (e) => {
        const rect = graphCanvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        for (const n of graphNodes) {
            const dist = Math.hypot(n.x - mx, n.y - my);
            if (dist < n.radius + 6) {
                draggedNode = n;
                n.isFixed = true;
                break;
            }
        }
    });

    window.addEventListener('mousemove', (e) => {
        if (!graphCanvas) return;
        const rect = graphCanvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        if (draggedNode) {
            draggedNode.x = mx;
            draggedNode.y = my;
            draggedNode.vx = 0;
            draggedNode.vy = 0;
            return;
        }

        hoveredNode = null;
        for (const n of graphNodes) {
            const dist = Math.hypot(n.x - mx, n.y - my);
            if (dist < n.radius + 6) {
                hoveredNode = n;
                break;
            }
        }
    });

    window.addEventListener('mouseup', () => {
        if (draggedNode) {
            draggedNode.isFixed = false;
            draggedNode = null;
        }
    });

    graphCanvas.addEventListener('click', (e) => {
        const rect = graphCanvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        for (const n of graphNodes) {
            const dist = Math.hypot(n.x - mx, n.y - my);
            if (dist < n.radius + 6) {
                inspectEvidenceModal(n.id);
                break;
            }
        }
    });

    runGraphSimulation();
}

function drawGraph() {
    const newNodes = [];
    const newEdges = [];
    const existingMap = new Map();
    for (const n of graphNodes) existingMap.set(n.id, n);

    const w = graphCanvas ? graphCanvas.width : 600;
    const h = graphCanvas ? graphCanvas.height : 520;

    for (const [id, entry] of forensicDB.graph.adjacencyList.entries()) {
        const existing = existingMap.get(id);
        const isDup = entry.vertex.status === 'DUPLICATE';

        const node = existing || {
            id: id,
            x: w / 2 + (Math.random() - 0.5) * 200,
            y: h / 2 + (Math.random() - 0.5) * 200,
            vx: 0,
            vy: 0,
            radius: 20,
            isFixed: false
        };
        node.vertex = entry.vertex;
        node.color = isDup ? '#ffb700' : '#00ff9d';
        newNodes.push(node);

        for (const edge of entry.edges) {
            if (id < edge.targetId) {
                newEdges.push({
                    sourceId: id,
                    targetId: edge.targetId,
                    weight: edge.weight,
                    type: edge.type,
                    label: edge.label
                });
            }
        }
    }

    graphNodes = newNodes;
    graphEdges = newEdges;
}

function runGraphSimulation() {
    if (!graphCtx || !graphCanvas) return;

    const w = graphCanvas.width;
    const h = graphCanvas.height;

    const repulsion = 1400;
    const springLen = 120;
    const springK = 0.04;
    const centerGravity = 0.015;
    const damping = 0.88;

    for (let i = 0; i < graphNodes.length; i++) {
        for (let j = i + 1; j < graphNodes.length; j++) {
            const n1 = graphNodes[i];
            const n2 = graphNodes[j];
            let dx = n2.x - n1.x;
            let dy = n2.y - n1.y;
            let dist = Math.hypot(dx, dy) || 1;
            if (dist < 300) {
                const force = repulsion / (dist * dist);
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                if (!n1.isFixed) { n1.vx -= fx; n1.vy -= fy; }
                if (!n2.isFixed) { n2.vx += fx; n2.vy += fy; }
            }
        }
    }

    const nodeMap = new Map();
    for (const n of graphNodes) nodeMap.set(n.id, n);

    for (const edge of graphEdges) {
        const s = nodeMap.get(edge.sourceId);
        const t = nodeMap.get(edge.targetId);
        if (s && t) {
            let dx = t.x - s.x;
            let dy = t.y - s.y;
            let dist = Math.hypot(dx, dy) || 1;
            const displacement = dist - springLen;
            const force = displacement * springK * edge.weight;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            if (!s.isFixed) { s.vx += fx; s.vy += fy; }
            if (!t.isFixed) { t.vx += fx; t.vy += fy; }
        }
    }

    for (const n of graphNodes) {
        if (!n.isFixed) {
            n.vx += (w / 2 - n.x) * centerGravity;
            n.vy += (h / 2 - n.y) * centerGravity;
            n.vx *= damping;
            n.vy *= damping;
            n.x += n.vx;
            n.y += n.vy;

            n.x = Math.max(n.radius + 10, Math.min(w - n.radius - 10, n.x));
            n.y = Math.max(n.radius + 10, Math.min(h - n.radius - 10, n.y));
        }
    }

    graphCtx.clearRect(0, 0, w, h);

    if (graphNodes.length === 0) {
        graphCtx.fillStyle = '#5e7394';
        graphCtx.font = '14px Rajdhani';
        graphCtx.textAlign = 'center';
        graphCtx.fillText('Evidence Graph Empty. Upload images to generate the relationship network.', w / 2, h / 2);
        requestAnimationFrame(runGraphSimulation);
        return;
    }

    for (const edge of graphEdges) {
        const s = nodeMap.get(edge.sourceId);
        const t = nodeMap.get(edge.targetId);
        if (s && t) {
            graphCtx.beginPath();
            graphCtx.moveTo(s.x, s.y);
            graphCtx.lineTo(t.x, t.y);

            const isExact = edge.type === 'EXACT_HASH';
            graphCtx.strokeStyle = isExact ? 'rgba(255, 51, 102, 0.7)' : 'rgba(0, 240, 255, 0.5)';
            graphCtx.lineWidth = edge.weight * 3.5;
            graphCtx.stroke();

            const mx = (s.x + t.x) / 2;
            const my = (s.y + t.y) / 2;
            graphCtx.fillStyle = isExact ? '#ff3366' : '#00f0ff';
            graphCtx.font = '9px Cascadia Mono';
            graphCtx.textAlign = 'center';
            graphCtx.fillText(edge.label, mx, my - 6);
        }
    }

    for (const n of graphNodes) {
        const isHovered = hoveredNode === n;

        graphCtx.save();
        graphCtx.shadowBlur = isHovered ? 20 : 10;
        graphCtx.shadowColor = n.color;

        graphCtx.beginPath();
        graphCtx.arc(n.x, n.y, isHovered ? n.radius + 4 : n.radius, 0, Math.PI * 2);
        graphCtx.fillStyle = '#060d1a';
        graphCtx.fill();
        graphCtx.lineWidth = 2.5;
        graphCtx.strokeStyle = n.color;
        graphCtx.stroke();
        graphCtx.restore();

        graphCtx.fillStyle = '#ffffff';
        graphCtx.font = 'bold 11px Rajdhani';
        graphCtx.textAlign = 'center';
        graphCtx.textBaseline = 'middle';
        graphCtx.fillText(n.id, n.x, n.y);

        graphCtx.fillStyle = '#94a9c9';
        graphCtx.font = '9px Cascadia Mono';
        graphCtx.fillText(n.vertex.status === 'DUPLICATE' ? 'DUP' : 'ORIG', n.x, n.y + n.radius + 12);
    }

    requestAnimationFrame(runGraphSimulation);
}

function resetGraphPhysics() {
    const w = graphCanvas.width;
    const h = graphCanvas.height;
    for (const n of graphNodes) {
        n.x = w / 2 + (Math.random() - 0.5) * 260;
        n.y = h / 2 + (Math.random() - 0.5) * 260;
        n.vx = 0;
        n.vy = 0;
        n.isFixed = false;
    }
    audio.playBlip();
    showToast('Graph physics stabilized', 'info');
}

async function runGraphBFS() {
    if (graphNodes.length === 0) return;
    const startNode = graphNodes[0];
    const order = forensicDB.graph.bfs(startNode.id);

    showToast(`Graph BFS Traversal starting from ${startNode.id}`, 'info');

    const nodeMap = new Map();
    for (const n of graphNodes) nodeMap.set(n.id, n);

    for (let i = 0; i < order.length; i++) {
        const node = nodeMap.get(order[i]);
        if (node) {
            const oldColor = node.color;
            node.color = '#ffffff';
            audio.play(500 + i * 50, 'sine', 0.1, 0.08);
            await new Promise(r => setTimeout(r, 400));
            node.color = oldColor;
        }
    }
    audio.playSuccess();
}

// =========================================================
// 12. DATA STRUCTURES LAB LIVE MEMORY VIEW
// =========================================================

function renderDSALab() {
    const hashContainer = document.getElementById('dsaHashTableLive');
    if (hashContainer) {
        let html = '';
        for (let i = 0; i < forensicDB.hashTable.size; i++) {
            const bucket = forensicDB.hashTable.buckets[i];
            html += `
                <div class="bucket-row">
                    <span class="bucket-idx">[#${i}]</span>
                    <div class="bucket-chain">
            `;
            if (bucket.length === 0) {
                html += `<span style="color: #475569; font-size: 10px;">NULL (empty)</span>`;
            } else {
                for (const item of bucket) {
                    const isDup = item.evidence.status === 'DUPLICATE';
                    html += `
                        <div class="bucket-node ${isDup ? 'dup' : ''}">
                            <strong>${item.evidence.id}</strong> → SHA-256: ${item.key.substr(0, 16)}...
                            <span style="font-size: 9px; opacity: 0.8;">(${item.evidence.status})</span>
                        </div>
                    `;
                }
            }
            html += `</div></div>`;
        }
        hashContainer.innerHTML = html;
    }

    const graphContainer = document.getElementById('dsaGraphAdjListLive');
    if (graphContainer) {
        let html = '';
        if (forensicDB.graph.adjacencyList.size === 0) {
            html = `<div style="color: #475569; padding: 20px; text-align: center;">Graph has no vertices yet.</div>`;
        } else {
            for (const [id, entry] of forensicDB.graph.adjacencyList.entries()) {
                html += `
                    <div class="adj-vertex">
                        <div class="vertex-head">VERTEX [${id}]: ${escapeHtml(entry.vertex.fileName)}</div>
                `;
                if (entry.edges.length === 0) {
                    html += `<div class="vertex-edge" style="color: #556987;">No incident edges</div>`;
                } else {
                    for (const edge of entry.edges) {
                        html += `
                            <div class="vertex-edge">
                                ↳ Edge to <strong>[${edge.targetId}]</strong> (Weight: ${edge.weight}, ${edge.label})
                            </div>
                        `;
                    }
                }
                html += `</div>`;
            }
        }
        graphContainer.innerHTML = html;
    }

    const treeContainer = document.getElementById('dsaTreeLive');
    if (treeContainer) {
        function buildTreeMemory(node) {
            const isRoot = node.id === 'ROOT';
            const indent = '&nbsp;&nbsp;&nbsp;&nbsp;'.repeat(node.depth);
            let out = `
                <div style="margin: 4px 0; font-size: 11px;">
                    ${indent}├─ <strong style="color: ${isRoot ? '#3b82f6' : node.data.status === 'DUPLICATE' ? '#ffb700' : '#00ff9d'};">[${node.id}]</strong>
                    ${isRoot ? 'Master Root' : escapeHtml(node.data.fileName)} 
                    <span style="color: #64748b; font-size: 10px;">(Depth: ${node.depth}, Children: ${node.children.length})</span>
                </div>
            `;
            for (const child of node.children) {
                out += buildTreeMemory(child);
            }
            return out;
        }
        treeContainer.innerHTML = buildTreeMemory(forensicDB.tree.root);
    }
}

// =========================================================
// 13. EVIDENCE INSPECTION MODAL (FULL DOSSIER)
// =========================================================

function inspectEvidenceModal(id) {
    const item = forensicDB.evidenceList.find(e => e.id === id);
    if (!item) return;

    audio.playBlip();

    const modal = document.getElementById('evidenceModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    if (modalTitle) modalTitle.textContent = `Forensic Dossier // ${item.id}`;

    const isDup = item.status === 'DUPLICATE';

    modalBody.innerHTML = `
        <div class="evidence-detail-grid">
            <div class="preview-panel">
                <img src="${item.dataUrl}" alt="Evidence Full">
            </div>

            <div>
                <div class="detail-card">
                    <div class="detail-row">
                        <span class="detail-label">EVIDENCE ID</span>
                        <span class="detail-value mono"><strong style="color: var(--neon-cyan);">${item.id}</strong></span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">FILE NAME</span>
                        <span class="detail-value">${escapeHtml(item.fileName)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">FILE SIZE</span>
                        <span class="detail-value">${item.fileSizeFormatted} (${item.fileSize.toLocaleString()} bytes)</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">RESOLUTION</span>
                        <span class="detail-value">${item.dimensions}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">ASPECT RATIO</span>
                        <span class="detail-value">${item.aspectRatio}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">STATUS</span>
                        <span class="detail-value">
                            <span class="status-badge ${isDup ? 'duplicate' : 'original'}">
                                ${isDup ? `DUPLICATE (${item.similarityScore}%)` : 'ORIGINAL'}
                            </span>
                        </span>
                    </div>
                    ${isDup ? `
                        <div class="detail-row">
                            <span class="detail-label">PARENT ROOT</span>
                            <span class="detail-value mono" style="color: var(--neon-amber);">
                                Parent Evidence: [${item.matchedParentId}] (${item.matchType})
                            </span>
                        </div>
                    ` : ''}
                    <div class="detail-row">
                        <span class="detail-label">STORAGE REFERENCE</span>
                        <span class="detail-value mono" style="color: ${item.isPhysicalCopy === 1 ? 'var(--neon-cyan)' : 'var(--neon-amber)'};">
                            ${item.isPhysicalCopy === 1 ? `💾 Unique physical copy (${item.storageFilename})` : `🔗 Deduplicated: Shared with [${item.matchedParentId}]`}
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">STORAGE PATH</span>
                        <span class="detail-value mono" style="font-size: 10px;">${escapeHtml(item.storagePath || 'storage/images/')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">SHA-256 HASH</span>
                        <span class="detail-value mono">${item.sha256}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">MD5 HASH</span>
                        <span class="detail-value mono">${item.md5}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">dHASH (64-bit)</span>
                        <span class="detail-value mono">${item.dHashHex}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">TIMESTAMP</span>
                        <span class="detail-value">${item.timestampFormatted}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">CUSTODY STATUS</span>
                        <span class="detail-value" style="color: var(--neon-green);">✓ ${item.custodyStatus}</span>
                    </div>
                </div>

                <div style="display: flex; gap: 10px; margin-top: 18px; flex-wrap: wrap;">
                    <button class="primary-button" onclick="copyText('${item.sha256}')" style="flex: 1; font-size: 12px; padding: 10px;">
                        Copy SHA-256
                    </button>
                    <button class="secondary-button" onclick="window.open('${item.dataUrl}', '_blank')" style="flex: 1; font-size: 12px; padding: 10px;">
                        Open Physical Image
                    </button>
                    <button class="secondary-button" onclick="deleteEvidence('${item.id}'); closeEvidenceModal();" style="flex: 1; font-size: 12px; padding: 10px; color: var(--neon-red); border-color: rgba(255, 51, 102, 0.4);">
                        Delete Evidence
                    </button>
                </div>
            </div>
        </div>
    `;

    modal.classList.add('open');
}

function closeEvidenceModal() {
    const modal = document.getElementById('evidenceModal');
    if (modal) modal.classList.remove('open');
}
