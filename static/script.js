// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    setupRecorderEvents(); 
});

// --- STATE VARIABLES ---
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// --- NAVIGATION LOGIC ---
function setActiveNav(id) {
    ['nav-transcribe', 'nav-history', 'nav-settings'].forEach(navId => {
        const btn = document.getElementById(navId);
        if(btn) btn.className = "w-full flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:bg-slate-800/50 border border-transparent transition-all";
    });

    const activeBtn = document.getElementById(id);
    if(activeBtn) activeBtn.className = "w-full flex items-center gap-3 px-3 py-3 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 transition-all";
}

// --- VIEW 1: RECORDER (HOME) ---
function renderRecorder() {
    setActiveNav('nav-transcribe');
    const contentArea = document.querySelector('.max-w-4xl');
    
    contentArea.innerHTML = `
        <div class="glass-card rounded-2xl p-8 text-center relative overflow-hidden group animate-fade-in">
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
            
            <div class="mb-6">
                <h1 class="text-3xl font-bold text-white mb-2">Capture Your Voice</h1>
                <p class="text-slate-400">Using OpenAI Whisper (Medium Model) • Force English Translation</p>
            </div>

            <div class="relative flex justify-center my-8">
                <button id="micBtn" class="w-24 h-24 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-2xl shadow-indigo-500/30 flex items-center justify-center transition-all duration-300 z-10">
                    <i data-lucide="mic" class="w-10 h-10"></i>
                </button>
                <div id="micRipple" class="absolute inset-0 m-auto w-24 h-24 rounded-full bg-indigo-600 opacity-0"></div>
            </div>

            <p id="micStatus" class="text-sm font-mono text-indigo-300">Press <kbd class="bg-slate-800 px-2 py-1 rounded border border-slate-700 mx-1 text-white">Space</kbd> to Record</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            <div class="md:col-span-3 glass-card rounded-xl border-dashed border-2 border-slate-700 hover:border-indigo-500 hover:bg-slate-800/50 transition-all p-6 flex flex-col items-center justify-center cursor-pointer relative">
                <input type="file" id="fileInput" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" accept="audio/*">
                <i data-lucide="upload-cloud" class="w-8 h-8 text-slate-500 mb-3"></i>
                <p class="text-sm text-slate-300 font-medium">Click to upload or drag audio file here</p>
                <p class="text-xs text-slate-500 mt-1">Supports MP3, WAV, M4A</p>
            </div>
        </div>

        <div id="resultSection" class="hidden mt-6 opacity-0 transition-opacity duration-500">
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-lg font-semibold text-white flex items-center gap-2">
                    <i data-lucide="terminal" class="w-5 h-5 text-green-400"></i> Transcription Output
                </h3>
                <button onclick="copyText('transcriptText')" class="text-xs flex items-center gap-1 text-slate-400 hover:text-white transition-colors">
                    <i data-lucide="copy"></i> Copy
                </button>
            </div>
            <div class="glass-card rounded-xl p-6 border-l-4 border-l-indigo-500 bg-[#0d1117]">
                <pre id="transcriptText" class="font-mono text-slate-300 whitespace-pre-wrap leading-relaxed text-sm"></pre>
            </div>
        </div>
    `;
    
    lucide.createIcons();
    setupRecorderEvents();
}

// --- VIEW 2: HISTORY LIST ---
async function renderHistory() {
    setActiveNav('nav-history');
    const contentArea = document.querySelector('.max-w-4xl');
    
    contentArea.innerHTML = `
        <div class="glass-card rounded-2xl p-8 animate-fade-in">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white">Transcription History</h2>
                <button onclick="renderRecorder()" class="text-sm text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i> Back to Recorder
                </button>
            </div>
            <div id="historyList" class="space-y-3">
                <div class="text-center text-slate-500 py-10 flex flex-col items-center">
                    <i data-lucide="loader-2" class="w-8 h-8 animate-spin mb-2"></i>
                    Loading...
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();

    try {
        const res = await fetch('/history');
        const data = await res.json();
        const listContainer = document.getElementById('historyList');
        
        if (data.length === 0) {
            listContainer.innerHTML = '<div class="text-center text-slate-500 py-10">No history found.</div>';
            return;
        }

        let html = '';
        data.forEach(item => {
            let statusColor = item.status === 'Completed' ? 'text-green-400 bg-green-400/10 border-green-500/20' : 
                              item.status === 'Failed' ? 'text-red-400 bg-red-400/10 border-red-500/20' : 
                              'text-amber-400 bg-amber-400/10 border-amber-500/20';

            // Added onclick to open details
            html += `
                <div onclick="openHistoryItem(${item.id})" class="cursor-pointer p-4 rounded-xl bg-slate-800/50 border border-slate-700 flex justify-between items-center hover:bg-slate-800 transition-colors group hover:border-indigo-500/50">
                    <div class="overflow-hidden">
                        <h4 class="font-medium text-slate-200 truncate">${item.filename}</h4>
                        <p class="text-xs text-slate-500 mt-1 truncate group-hover:text-slate-300 transition-colors font-mono">${item.transcript || "Processing..."}</p>
                    </div>
                    <span class="px-3 py-1 rounded-full text-xs font-medium border ${statusColor} ml-4 whitespace-nowrap flex items-center gap-2">
                        ${item.status === 'Completed' ? '<i data-lucide="eye" class="w-3 h-3"></i>' : ''}
                        ${item.status}
                    </span>
                </div>
            `;
        });
        listContainer.innerHTML = html;
        lucide.createIcons();

    } catch (err) {
        console.error(err);
        document.getElementById('historyList').innerHTML = '<div class="text-center text-red-400">Error loading history.</div>';
    }
}

// --- VIEW 2.1: HISTORY DETAIL (NEW FEATURE) ---
async function openHistoryItem(id) {
    const contentArea = document.querySelector('.max-w-4xl');
    
    // Show loading state
    contentArea.innerHTML = `
        <div class="glass-card rounded-2xl p-10 text-center">
            <i data-lucide="loader-2" class="w-8 h-8 animate-spin text-indigo-500 mx-auto mb-3"></i>
            <p class="text-slate-400">Fetching transcript...</p>
        </div>
    `;
    lucide.createIcons();

    try {
        // Fetch full transcript using existing status API
        const res = await fetch(`/status/${id}`);
        const data = await res.json();

        contentArea.innerHTML = `
            <div class="glass-card rounded-2xl p-8 animate-fade-in">
                <div class="flex items-center justify-between mb-6 pb-6 border-b border-slate-700/50">
                    <div>
                        <h2 class="text-2xl font-bold text-white">Transcript Details</h2>
                        <p class="text-xs text-slate-500 mt-1 font-mono">ID: #${id} • Status: ${data.status}</p>
                    </div>
                    <div class="flex gap-3">
                        <button onclick="copyText('fullTranscript')" class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors flex items-center gap-2">
                            <i data-lucide="copy" class="w-4 h-4"></i> Copy Text
                        </button>
                        <button onclick="renderHistory()" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors flex items-center gap-2">
                            <i data-lucide="arrow-left" class="w-4 h-4"></i> Back
                        </button>
                    </div>
                </div>

                <div class="bg-[#0d1117] rounded-xl p-6 border border-slate-700/50 relative shadow-inner">
                    <pre id="fullTranscript" class="font-mono text-slate-300 whitespace-pre-wrap leading-relaxed text-sm min-h-[200px] max-h-[60vh] overflow-y-auto">${data.transcript || "No transcript available yet."}</pre>
                </div>
            </div>
        `;
        lucide.createIcons();

    } catch (err) {
        alert("Error fetching transcript details");
        renderHistory(); // Go back on error
    }
}

// --- VIEW 3: SETTINGS ---
function renderSettings() {
    setActiveNav('nav-settings');
    const contentArea = document.querySelector('.max-w-4xl');

    contentArea.innerHTML = `
        <div class="glass-card rounded-2xl p-8 animate-fade-in">
            <div class="flex items-center justify-between mb-8">
                <div>
                    <h2 class="text-2xl font-bold text-white">System Preferences</h2>
                    <p class="text-slate-400 text-sm mt-1">Manage AI behavior and application settings</p>
                </div>
                <button onclick="renderRecorder()" class="text-sm text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i> Back
                </button>
            </div>

            <div class="space-y-8">
                <div>
                    <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">AI Configuration</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-medium text-slate-300 mb-2">Whisper Model</label>
                            <select class="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none">
                                <option value="tiny">Tiny</option>
                                <option value="small" selected>Small (Optimized)</option>
                                <option value="medium">Medium (High Accuracy)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-slate-300 mb-2">Language</label>
                            <select class="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none">
                                <option value="en" selected>Force English</option>
                                <option value="hi">Hindi</option>
                                <option value="auto">Auto-Detect</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="flex justify-end gap-4 pt-4 border-t border-slate-700/50">
                    <button class="px-4 py-2 rounded-lg text-slate-400 hover:text-white transition-colors" onclick="renderRecorder()">Cancel</button>
                    <button onclick="saveSettings()" class="px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg flex items-center gap-2">
                        <i data-lucide="save" class="w-4 h-4"></i> Save Changes
                    </button>
                </div>
            </div>
        </div>
    `;
    lucide.createIcons();
}

function saveSettings() {
    const btn = document.querySelector('button[onclick="saveSettings()"]');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Saving...';
    lucide.createIcons();
    
    setTimeout(() => {
        btn.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i> Saved!';
        btn.classList.replace('bg-indigo-600', 'bg-green-600');
        lucide.createIcons();
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.replace('bg-green-600', 'bg-indigo-600');
            lucide.createIcons();
        }, 2000);
    }, 800);
}

// --- RECORDING & UPLOAD LOGIC ---
function setupRecorderEvents() {
    const micBtn = document.getElementById('micBtn');
    if(micBtn) micBtn.addEventListener('click', toggleRecording);
    
    const fileInput = document.getElementById('fileInput');
    if(fileInput) fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) uploadAudio(e.target.files[0], e.target.files[0].name);
    });
}

async function toggleRecording() {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                uploadAudio(audioBlob, "mic_recording.wav");
                stream.getTracks().forEach(track => track.stop());
            };
            mediaRecorder.start();
            isRecording = true;
            
            const micBtn = document.getElementById('micBtn');
            if(micBtn) {
                micBtn.classList.add('mic-active');
                micBtn.innerHTML = '<i data-lucide="square" class="w-8 h-8 fill-current"></i>';
                micBtn.classList.replace('bg-indigo-600', 'bg-red-500');
            }
            document.getElementById('micStatus').textContent = "Recording... Press Space to Stop";
            updateStatus("Recording Live", "error");
            lucide.createIcons();

        } catch (err) { alert("Mic Access Denied!"); }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        renderRecorderState();
    }
}

function renderRecorderState() {
    const micBtn = document.getElementById('micBtn');
    if(micBtn) {
        micBtn.classList.remove('mic-active');
        micBtn.innerHTML = '<i data-lucide="mic" class="w-10 h-10"></i>';
        micBtn.classList.replace('bg-red-500', 'bg-indigo-600');
    }
    const status = document.getElementById('micStatus');
    if(status) status.textContent = "Press Space to Record";
    lucide.createIcons();
}

// --- HOTKEY ---
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && document.getElementById('micBtn')) {
        e.preventDefault();
        toggleRecording();
    }
});

// --- UPLOAD API ---
async function uploadAudio(fileOrBlob, filename) {
    updateStatus("Uploading...", "processing");
    const formData = new FormData();
    formData.append('audio', fileOrBlob, filename);

    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        updateStatus("AI Processing...", "processing");
        pollStatus(data.job_id);
    } catch (err) {
        updateStatus("Error", "error");
    }
}

function pollStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/status/${jobId}`);
            const data = await res.json();
            if (data.status === 'Completed') {
                clearInterval(interval);
                updateStatus("System Ready", "success");
                
                const resultSection = document.getElementById('resultSection');
                if(resultSection) {
                    document.getElementById('transcriptText').textContent = data.transcript;
                    resultSection.classList.remove('hidden');
                    setTimeout(() => resultSection.classList.add('opacity-100'), 50);
                }
            } else if (data.status === 'Failed') {
                clearInterval(interval);
                updateStatus("Transcription Failed", "error");
            }
        } catch (e) { clearInterval(interval); }
    }, 2000);
}

function updateStatus(msg, type) {
    const badge = document.getElementById('statusBadge');
    if(badge) {
        badge.textContent = msg;
        badge.className = `px-3 py-1 rounded-full text-xs font-medium border transition-all duration-300 ${
            type === 'processing' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse' :
            type === 'success' ? 'bg-slate-800 text-slate-400 border-slate-700' :
            type === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
            'bg-slate-800 text-slate-400 border-slate-700'
        }`;
    }
}

function copyText(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text);
    alert("Copied!");
}