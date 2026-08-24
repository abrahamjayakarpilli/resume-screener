// TalentLens AI API Client Wrapper

const BASE_URL = ""; // Relative path to backend server on same origin

const API = {
    async getHealth() {
        const res = await fetch(`${BASE_URL}/api/health`);
        return res.json();
    },

    async getJobs() {
        const res = await fetch(`${BASE_URL}/api/jobs`);
        if (!res.ok) throw new Error("Failed to fetch jobs");
        return res.json();
    },

    async getJob(id) {
        const res = await fetch(`${BASE_URL}/api/jobs/${id}`);
        if (!res.ok) throw new Error("Failed to fetch job details");
        return res.json();
    },

    async createJob(payload) {
        const res = await fetch(`${BASE_URL}/api/jobs`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Failed to create job profile");
        return res.json();
    },

    async screenResumes(jobId, files) {
        const formData = new FormData();
        for (const file of files) {
            formData.append("files", file);
        }
        
        const res = await fetch(`${BASE_URL}/api/jobs/${jobId}/screen`, {
            method: "POST",
            body: formData
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Failed to screen resumes");
        }
        return res.json();
    },

    async getScreeningRun(id) {
        const res = await fetch(`${BASE_URL}/api/screening-runs/${id}`);
        if (!res.ok) throw new Error("Failed to fetch screening run status");
        return res.json();
    },

    async getScreeningRuns() {
        const res = await fetch(`${BASE_URL}/api/screening-runs`);
        if (!res.ok) throw new Error("Failed to fetch screening runs");
        return res.json();
    },

    async getCandidate(id) {
        const res = await fetch(`${BASE_URL}/api/candidates/${id}`);
        if (!res.ok) throw new Error("Failed to fetch candidate details");
        return res.json();
    },

    async getMatch(id) {
        const res = await fetch(`${BASE_URL}/api/matches/${id}`);
        if (!res.ok) throw new Error("Failed to fetch match metrics");
        return res.json();
    },

    async getMatchSensitivity(matchId) {
        const res = await fetch(`${BASE_URL}/api/matches/${matchId}/sensitivity`);
        if (!res.ok) throw new Error("Failed to fetch match sensitivity profile");
        return res.json();
    },

    async compareCandidates(candidateIds) {
        const res = await fetch(`${BASE_URL}/api/candidates/compare`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate_ids: candidateIds })
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Failed to run candidate comparison");
        }
        return res.json();
    }
};
