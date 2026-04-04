// Application State
let currentTask = null;
let currentState = null;

// DOM Elements
const taskListEl = document.getElementById('task-list');
const resetBtn = document.getElementById('reset-btn');
const activeCaseEl = document.getElementById('active-case');
const currentRewardEl = document.getElementById('current-reward');
const currentDifficultyEl = document.getElementById('current-difficulty');
const badgeEl = document.getElementById('case-status-badge');
const actionForm = document.getElementById('action-form');
const applicantData = document.getElementById('applicant-data');
const taskDesc = document.getElementById('task-desc');
const resultOverlay = document.getElementById('result-overlay');
const finalReward = document.getElementById('final-reward');
const nextCaseBtn = document.getElementById('next-case-btn');

// Initialize
async function fetchTasks() {
    try {
        const res = await fetch('/tasks');
        const tasks = await res.json();
        renderTasks(tasks);
    } catch (e) {
        console.error("Failed to fetch API tasks", e);
    }
}

function renderTasks(tasks) {
    taskListEl.innerHTML = '';
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = 'task-item';
        li.innerHTML = `<strong>${task.id.toUpperCase()}</strong><span>${task.description}</span>`;
        li.onclick = () => selectTask(task.id, li);
        taskListEl.appendChild(li);
    });
}

function selectTask(taskId, element) {
    document.querySelectorAll('.task-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    currentTask = taskId;
    resetBtn.disabled = false;
    currentDifficultyEl.innerText = taskId.toUpperCase();
}

resetBtn.onclick = async () => {
    if (!currentTask) return;
    try {
        resetBtn.innerText = "Initializing...";
        const res = await fetch('/reset', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task: currentTask})
        });
        currentState = await res.json();
        updateUI();
    } catch (e) {
        alert("Server error connecting to backend.");
    } finally {
        resetBtn.innerText = "Initialize Environment";
    }
};

function updateUI() {
    if (!currentState) return;
    
    // Update Sidebar
    activeCaseEl.innerText = currentState.case_id;
    currentRewardEl.innerText = currentState.partial_score.toFixed(1);
    badgeEl.innerText = currentState.is_done ? "Episode Complete" : `Active Case: ${currentState.case_id}`;

    // Update Profile
    taskDesc.innerText = currentState.task_description;
    applicantData.innerHTML = '';
    
    for (const [key, val] of Object.entries(currentState.applicant_profile)) {
        const titleCaseKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const row = document.createElement('div');
        row.className = 'data-row';
        row.innerHTML = `<span class="label">${titleCaseKey}</span><span class="val">${val}</span>`;
        applicantData.appendChild(row);
    }
    
    applicantData.classList.remove('hidden');
    actionForm.classList.remove('hidden');
    resultOverlay.classList.add('hidden');
    actionForm.reset();
}

actionForm.onsubmit = async (e) => {
    e.preventDefault();
    
    const decision = document.getElementById('action-decision').value;
    const riskOpts = document.querySelector('input[name="risk"]:checked');
    const confOpts = document.querySelector('input[name="confidence"]:checked');
    
    const criteriaStr = document.getElementById('action-criteria').value;
    const flagsStr = document.getElementById('action-flags').value;
    
    const payload = {
        decision: decision,
        risk_level: riskOpts ? riskOpts.value : "medium",
        confidence: confOpts ? confOpts.value : "medium",
        failed_criteria: criteriaStr ? criteriaStr.split(',').map(s=>s.trim()) : [],
        flags: flagsStr ? flagsStr.split(',').map(s=>s.trim()) : []
    };

    try {
        const res = await fetch('/step', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        showResult(result);
    } catch(err) {
        alert("Error sending action.");
    }
};

function showResult(result) {
    actionForm.classList.add('hidden');
    resultOverlay.classList.remove('hidden');
    const rewardFormated = result.reward >= 0 ? `+${result.reward.toFixed(2)}` : result.reward.toFixed(2);
    finalReward.innerText = rewardFormated;
    
    if(result.reward > 0) {
        finalReward.style.color = "var(--accent)";
        document.querySelector('.reward-circle').style.borderColor = "var(--accent)";
        document.querySelector('.reward-circle').style.boxShadow = "0 0 30px var(--accent-glow)";
    } else {
        finalReward.style.color = "var(--danger)";
        document.querySelector('.reward-circle').style.borderColor = "var(--danger)";
        document.querySelector('.reward-circle').style.boxShadow = "0 0 30px rgba(239, 68, 68, 0.4)";
    }
    
    // Auto sync state for score total
    setTimeout(async () => {
        const stateRes = await fetch('/state');
        const s = await stateRes.json();
        currentRewardEl.innerText = s.partial_score.toFixed(1);
    }, 500);
}

nextCaseBtn.onclick = () => {
    resetBtn.click();
};

// Start
fetchTasks();
