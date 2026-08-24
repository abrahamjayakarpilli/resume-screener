// TalentLens AI — Single Page Application State Controller

document.addEventListener("DOMContentLoaded", () => {
    // State variables
    let currentView = "dashboard";
    let selectedCandidateIds = [];
    let allCandidates = [];
    let allJobs = [];
    let activeJobId = null;
    let selectedFiles = [];

    // DOM Element References
    const pageTitle = document.getElementById("page-title");
    const views = {
        dashboard: document.getElementById("view-dashboard"),
        jobs: document.getElementById("view-jobs"),
        candidates: document.getElementById("view-candidates"),
        compare: document.getElementById("view-comparison"),
        details: document.getElementById("view-candidate-details")
    };

    const navs = {
        dashboard: document.getElementById("nav-dashboard"),
        jobs: document.getElementById("nav-jobs"),
        candidates: document.getElementById("nav-candidates"),
        compare: document.getElementById("nav-compare")
    };

    // Modals
    const modals = {
        job: document.getElementById("modal-create-job"),
        upload: document.getElementById("modal-upload-resumes")
    };

    // Initialize SPA Views Router
    function navigateTo(viewId) {
        currentView = viewId;
        
        // Hide all views, deactivate nav items
        Object.keys(views).forEach(key => {
            if (views[key]) views[key].style.display = "none";
        });
        Object.keys(navs).forEach(key => {
            if (navs[key]) navs[key].classList.remove("active");
        });

        // Show target view, activate nav item
        if (views[viewId]) views[viewId].style.display = "flex";
        
        // Handle detail view maps to candidates menu highlighting
        let navKey = viewId;
        if (viewId === "details") navKey = "candidates";
        if (navs[navKey]) navs[navKey].classList.add("active");

        // Set Title
        const titles = {
            dashboard: "Dashboard Overview",
            jobs: "Available Job Profiles",
            candidates: "Candidate Intelligence Directory",
            compare: "Side-by-Side Comparison Matrix",
            details: "Candidate Match Profile"
        };
        pageTitle.innerText = titles[viewId] || "TalentLens AI";

        // Fetch fresh data based on view
        if (viewId === "dashboard") {
            loadDashboardData();
        } else if (viewId === "jobs") {
            loadJobsData();
        } else if (viewId === "candidates") {
            loadCandidatesData();
        }
    }

    // Bind hash change routing
    window.addEventListener("hashchange", () => {
        const hash = window.location.hash.substring(1) || "dashboard";
        if (hash.startsWith("candidate/")) {
            const candId = hash.split("/")[1];
            showCandidateDetails(candId);
        } else {
            navigateTo(hash);
        }
    });

    // Handle initial load routing
    const initialHash = window.location.hash.substring(1) || "dashboard";
    if (initialHash.startsWith("candidate/")) {
        const candId = initialHash.split("/")[1];
        showCandidateDetails(candId);
    } else {
        navigateTo(initialHash);
    }

    // Sidebar navigation clicks
    Object.keys(navs).forEach(key => {
        if (navs[key]) {
            navs[key].addEventListener("click", (e) => {
                e.preventDefault();
                window.location.hash = key;
            });
        }
    });

    // MODAL TRIGGERS
    document.getElementById("btn-create-job-modal").onclick = () => modals.job.style.display = "flex";
    document.getElementById("btn-close-job-modal").onclick = () => modals.job.style.display = "none";
    document.getElementById("btn-cancel-job-modal").onclick = () => modals.job.style.display = "none";

    document.getElementById("btn-upload-resumes-modal").onclick = () => {
        populateJobSelectDropdown();
        modals.upload.style.display = "flex";
    };
    document.getElementById("btn-close-upload-modal").onclick = () => resetUploadModal();
    document.getElementById("btn-cancel-upload-modal").onclick = () => resetUploadModal();

    // DYNAMIC DATA LOADERS

    // 1. Dashboard data
    async function loadDashboardData() {
        try {
            const jobs = await API.getJobs();
            allJobs = jobs;

            const runs = await API.getScreeningRuns();
            
            // Collect all matches from runs
            let totalMatches = 0;
            let shortlisted = 0;
            let needsReview = 0;
            let scoreSum = 0.0;
            let matchCount = 0;
            let allMatches = [];

            runs.forEach(r => {
                r.matches.forEach(m => {
                    totalMatches++;
                    if (m.recommendation === "SHORTLIST") shortlisted++;
                    else if (m.recommendation === "REVIEW") needsReview++;
                    scoreSum += m.overall_score;
                    matchCount++;
                    allMatches.push(m);
                });
            });

            // Empty state handling
            let emptyEl = document.getElementById("dashboard-empty-state");
            if (totalMatches === 0) {
                document.getElementById("metric-total-candidates").innerText = "—";
                document.getElementById("metric-shortlisted").innerText = "—";
                document.getElementById("metric-needs-review").innerText = "—";
                document.getElementById("metric-avg-score").innerText = "—";

                document.getElementById("dashboard-main-layouts").style.display = "none";
                if (!emptyEl) {
                    emptyEl = document.createElement("div");
                    emptyEl.id = "dashboard-empty-state";
                    emptyEl.className = "empty-state-panel";
                    document.getElementById("view-dashboard").appendChild(emptyEl);
                }
                emptyEl.style.display = "flex";
                emptyEl.innerHTML = `
                    <i data-lucide="folder-search" class="empty-icon"></i>
                    <h3>No Screening Runs Recorded Yet</h3>
                    <p>Register a job profile and upload resumes to run candidate matching and unlock intelligence reports here.</p>
                    <div class="empty-actions">
                        <button class="btn btn-primary" id="btn-empty-create-job"><i data-lucide="plus-circle" style="width:14px; height:14px; margin-right:6px; vertical-align:middle; display:inline-block;"></i>Create Job</button>
                        <button class="btn btn-outline" id="btn-empty-demo-run"><i data-lucide="play" style="width:14px; height:14px; margin-right:6px; vertical-align:middle; display:inline-block;"></i>Run Demo Run</button>
                    </div>
                `;
                document.getElementById("btn-empty-create-job").onclick = () => modals.job.style.display = "flex";
                document.getElementById("btn-empty-demo-run").onclick = () => {
                    document.getElementById("btn-quick-run-demo").click();
                };
                lucide.createIcons();
                return;
            }

            if (emptyEl) emptyEl.style.display = "none";
            document.getElementById("dashboard-main-layouts").style.display = "grid";

            document.getElementById("metric-total-candidates").innerText = totalMatches;
            document.getElementById("metric-shortlisted").innerText = shortlisted;
            document.getElementById("metric-needs-review").innerText = needsReview;
            
            const avgScore = matchCount > 0 ? Math.round(scoreSum / matchCount) : 0;
            document.getElementById("metric-avg-score").innerText = `${avgScore}%`;

            // 1. Render Top Candidate Rankings (Recent run or overall)
            const rankingList = document.getElementById("dashboard-rankings-list");
            rankingList.innerHTML = "";
            
            const sortedMatches = [...allMatches].sort((a, b) => b.overall_score - a.overall_score).slice(0, 5);
            sortedMatches.forEach((m, idx) => {
                const isDemo = ["John Doe", "Jane Smith", "Bob Jones", "Alice White", "Charlie Brown"].includes(m.candidate.name);
                rankingList.innerHTML += `
                    <div class="ranking-item" onclick="window.location.hash='#candidate/${m.candidate.id}'">
                        <div class="ranking-item-left">
                            <span class="ranking-rank">#${idx + 1}</span>
                            <span class="ranking-name">${m.candidate.name} ${isDemo ? '<span class="badge badge-outline" style="font-size: 8px; padding: 1px 4px; margin-left: 6px; color:#6B7280; border-color:#D1D5DB; font-weight:500;">DEMO DATA</span>' : ''}</span>
                        </div>
                        <span class="ranking-score">${Math.round(m.overall_score)}%</span>
                    </div>
                `;
            });

            // 2. Render Recruiter Insights
            const insightsList = document.getElementById("dashboard-insights-list");
            insightsList.innerHTML = "";
            const insights = [];

            const topMatch = sortedMatches[0];
            if (topMatch) {
                const isDemo = ["John Doe", "Jane Smith", "Bob Jones", "Alice White", "Charlie Brown"].includes(topMatch.candidate.name);
                insights.push(`
                    <i data-lucide="award" class="insight-icon" style="color:var(--color-primary);"></i>
                    <span><strong>${topMatch.candidate.name}</strong> ${isDemo ? '(Demo)' : ''} has the strongest technical suitability match (${Math.round(topMatch.overall_score)}%).</span>
                `);
            }
            if (shortlisted > 0) {
                insights.push(`
                    <i data-lucide="check-circle" class="insight-icon" style="color:var(--color-success);"></i>
                    <span>${shortlisted} candidate(s) meet all critical job requirements and are shortlisted.</span>
                `);
            }
            
            // Overlapping timeline warnings count
            const timelineWarningsCount = allMatches.filter(m => {
                try {
                    const w = JSON.parse(m.candidate.timeline_issues || "[]");
                    return w && w.length > 0;
                } catch(e) { return false; }
            }).length;
            if (timelineWarningsCount > 0) {
                insights.push(`
                    <i data-lucide="alert-triangle" class="insight-icon" style="color:var(--color-warning);"></i>
                    <span>${timelineWarningsCount} candidate(s) have concurrent employment/study overlaps flagged for review.</span>
                `);
            }

            // Incomplete profiles count
            const incompleteCount = allMatches.filter(m => m.candidate.completeness_score < 70).length;
            if (incompleteCount > 0) {
                insights.push(`
                    <i data-lucide="help-circle" class="insight-icon" style="color:var(--color-text-muted);"></i>
                    <span>${incompleteCount} profile(s) have missing contact or history details (completeness &lt; 70%).</span>
                `);
            }

            // AWS missing count
            let missingAwsCount = 0;
            allMatches.forEach(m => {
                const awsReq = m.match_requirements?.find(mr => mr.requirement?.requirement_text?.toLowerCase().includes("aws"));
                if (awsReq && (awsReq.status === "MISSING" || awsReq.status === "NO EVIDENCE")) {
                    missingAwsCount++;
                }
            });
            if (missingAwsCount > 0) {
                insights.push(`
                    <i data-lucide="info" class="insight-icon" style="color:var(--color-info);"></i>
                    <span>${missingAwsCount} candidate(s) have no evidence of AWS experience in their resumes.</span>
                `);
            }

            insightsList.innerHTML = insights.map(ins => `<div class="insight-item">${ins}</div>`).join("");

            // 3. Requirement Coverage List for the most recent run
            const coverageList = document.getElementById("dashboard-coverage-list");
            coverageList.innerHTML = "";
            
            const recentRun = [...runs].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];
            if (recentRun && recentRun.matches.length > 0) {
                const runMatches = recentRun.matches;
                const jobRequirements = recentRun.matches[0].match_requirements.map(mr => mr.requirement);
                
                // Keep unique requirements
                const uniqueReqs = [];
                const seenReqs = new Set();
                jobRequirements.forEach(req => {
                    if (req && !seenReqs.has(req.id)) {
                        seenReqs.add(req.id);
                        uniqueReqs.push(req);
                    }
                });

                uniqueReqs.slice(0, 5).forEach(req => {
                    let matchOrPartial = 0;
                    runMatches.forEach(m => {
                        const mr = m.match_requirements.find(x => x.requirement_id === req.id);
                        if (mr && (mr.status === "MATCH" || mr.status === "PARTIAL")) {
                            matchOrPartial++;
                        }
                    });
                    const pct = Math.round((matchOrPartial / runMatches.length) * 100);
                    coverageList.innerHTML += `
                        <div class="coverage-item">
                            <div class="coverage-lbl">
                                <span>${req.requirement_text}</span>
                                <span>${pct}%</span>
                            </div>
                            <div class="coverage-bar-bg">
                                <div class="coverage-bar-fill" style="width: ${pct}%;"></div>
                            </div>
                        </div>
                    `;
                });
            } else {
                coverageList.innerHTML = `<p class="quick-action-tip" style="text-align:center;">No recent coverage metrics available.</p>`;
            }

            // 4. Render Recent Runs Table
            const tbody = document.querySelector("#table-recent-runs tbody");
            tbody.innerHTML = "";

            const sortedRuns = [...runs].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);

            sortedRuns.forEach(run => {
                const runDate = new Date(run.created_at).toLocaleDateString();
                const job = allJobs.find(j => j.id === run.job_id);
                const jobTitle = job ? job.title : "Backend Engineer";
                const isDemo = run.name.toLowerCase().includes("demo") || jobTitle.toLowerCase().includes("demo") || (run.matches[0] && ["John Doe", "Jane Smith", "Bob Jones"].includes(run.matches[0].candidate.name));

                let badgeClass = "badge-info";
                if (run.status === "completed") badgeClass = "badge-success";
                else if (run.status === "failed") badgeClass = "badge-danger";

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${run.name}</strong> ${isDemo ? '<span class="badge badge-outline" style="font-size: 8px; padding: 1px 4px; color:#6B7280; border-color:#D1D5DB; font-weight:500;">DEMO DATA</span>' : ''}</td>
                        <td>${jobTitle}</td>
                        <td><span class="badge ${badgeClass}">${run.status.toUpperCase()}</span></td>
                        <td>${runDate}</td>
                        <td>
                            <button class="btn btn-outline btn-sm" onclick="window.location.hash='candidates';"><i data-lucide="eye" style="width:12px; height:12px; margin-right:4px; display:inline-block; vertical-align:middle;"></i>Inspect Run</button>
                        </td>
                    </tr>
                `;
            });

            // Reinitialize vector icons
            lucide.createIcons();
        } catch (e) {
            console.error(e);
        }
    }

    // 2. Jobs list data
    async function loadJobsData() {
        try {
            const jobs = await API.getJobs();
            const tbody = document.querySelector("#table-jobs-list tbody");
            tbody.innerHTML = "";

            if (jobs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="quick-action-tip" style="text-align:center;">No jobs registered yet. Click '+ Create Job' to begin.</td></tr>`;
                return;
            }

            jobs.forEach(job => {
                const date = new Date(job.created_at).toLocaleDateString();
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${job.title}</strong></td>
                        <td>${job.department || "N/A"}</td>
                        <td>${job.requirements.length} requirements</td>
                        <td>${date}</td>
                        <td>
                            <button class="btn btn-outline btn-sm" onclick="document.getElementById('btn-upload-resumes-modal').click();">Screen Resumes</button>
                        </td>
                    </tr>
                `;
            });
        } catch (e) {
            console.error(e);
        }
    }

    // 3. Candidates Directory list data
    async function loadCandidatesData() {
        try {
            const jobs = await API.getJobs();
            allJobs = jobs;

            const runs = await API.getScreeningRuns();
            const jobFilter = document.getElementById("filter-job");
            const statusFilter = document.getElementById("filter-status");

            // Fill job dropdown filters
            const selectedJobVal = jobFilter.value;
            jobFilter.innerHTML = `<option value="all">All Jobs</option>`;
            
            allJobs.forEach(job => {
                jobFilter.innerHTML += `<option value="${job.id}">${job.title}</option>`;
            });
            jobFilter.value = selectedJobVal;

            // Collect all matches and bind metadata
            let listData = [];
            runs.forEach(run => {
                const job = allJobs.find(j => j.id === run.job_id);
                run.matches.forEach(match => {
                    match.job_id = run.job_id;
                    match.job_title = job ? job.title : "Unknown Job";
                    listData.push(match);
                });
            });

            // Sort by overall score descending
            listData.sort((a, b) => b.overall_score - a.overall_score);
            allCandidates = listData;

            renderCandidatesTable();
        } catch (e) {
            console.error(e);
        }
    }

    function renderCandidatesTable() {
        const jobVal = document.getElementById("filter-job").value;
        const statusVal = document.getElementById("filter-status").value;
        const tbody = document.querySelector("#table-candidates-list tbody");
        tbody.innerHTML = "";

        // Apply filters
        const filtered = allCandidates.filter(m => {
            const matchesJob = jobVal === "all" || m.job_id.toString() === jobVal;
            const matchesStatus = statusVal === "all" || m.recommendation === statusVal;
            return matchesJob && matchesStatus;
        });

        if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="quick-action-tip" style="text-align:center;">No candidates match the selected filters.</td></tr>`;
            return;
        }

        filtered.forEach((m, idx) => {
            const c = m.candidate;
            const rank = idx + 1;
            
            // Checkbox selection state
            const isChecked = selectedCandidateIds.includes(c.id) ? "checked" : "";
            
            // Recommendation styling
            let recClass = "badge-outline";
            if (m.recommendation === "SHORTLIST") recClass = "badge-success";
            else if (m.recommendation === "REVIEW") recClass = "badge-warning";
            else if (m.recommendation === "NOT RECOMMENDED") recClass = "badge-danger";

            // Skills extracting
            const topSkills = c.candidate_skills.slice(0, 3).map(cs => cs.skill.name).join(", ");
            
            // Timeline Issues
            let timelineText = '<span style="color: var(--color-success);"><i data-lucide="check" style="width:12px; height:12px; display:inline-block; vertical-align:middle; margin-right:4px;"></i>None</span>';
            if (c.timeline_issues) {
                const issues = JSON.parse(c.timeline_issues);
                if (issues.length > 0) {
                    timelineText = `<span class="badge badge-warning"><i data-lucide="alert-triangle" style="width:12px; height:12px; display:inline-block; vertical-align:middle; margin-right:4px;"></i>Flagged</span>`;
                }
            }

            const isDemo = ["John Doe", "Jane Smith", "Bob Jones", "Alice White", "Charlie Brown"].includes(c.name);
            const demoBadge = isDemo ? ' <span class="badge badge-outline" style="font-size: 8px; padding: 1px 4px; color:#6B7280; border-color:#D1D5DB; font-weight:500; margin-left:6px; vertical-align:middle;">DEMO DATA</span>' : '';

            tbody.innerHTML += `
                <tr>
                    <td>
                        <input type="checkbox" class="compare-checkbox" data-id="${c.id}" ${isChecked}>
                    </td>
                    <td><strong>#${rank}</strong></td>
                    <td><strong>${c.name}</strong>${demoBadge}</td>
                    <td><strong style="color: var(--color-primary);">${m.overall_score}%</strong></td>
                    <td><span class="badge ${recClass}">${m.recommendation}</span></td>
                    <td>${c.experience_years.toFixed(1)} yrs</td>
                    <td>${topSkills || "N/A"}</td>
                    <td>${timelineText}</td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="window.location.hash='candidate/${c.id}'"><i data-lucide="eye" style="width:12px; height:12px; margin-right:4px; display:inline-block; vertical-align:middle;"></i>Inspect</button>
                    </td>
                </tr>
            `;
        });

        // Initialize Lucide icons on dynamic content
        lucide.createIcons();

        // Add checkbox change event listeners
        document.querySelectorAll(".compare-checkbox").forEach(chk => {
            chk.addEventListener("change", (e) => {
                const id = parseInt(e.target.dataset.id);
                if (e.target.checked) {
                    if (selectedCandidateIds.length >= 4) {
                        e.target.checked = false;
                        alert("You can select a maximum of 4 candidates to compare.");
                        return;
                    }
                    if (!selectedCandidateIds.includes(id)) {
                        selectedCandidateIds.push(id);
                    }
                } else {
                    selectedCandidateIds = selectedCandidateIds.filter(cid => cid !== id);
                }
                updateCompareBar();
            });
        });
    }

    // Filters behavior
    document.getElementById("filter-job").onchange = renderCandidatesTable;
    document.getElementById("filter-status").onchange = renderCandidatesTable;
    document.getElementById("btn-clear-filters").onclick = () => {
        document.getElementById("filter-job").value = "all";
        document.getElementById("filter-status").value = "all";
        renderCandidatesTable();
    };

    // Compare Selection Bar update
    function updateCompareBar() {
        const count = selectedCandidateIds.length;
        const badge = document.getElementById("compare-count");
        const compareBtn = document.getElementById("btn-run-comparison");
        const selectionText = document.getElementById("compare-selection-text");

        if (count > 0) {
            badge.innerText = count;
            badge.style.display = "inline-block";
        } else {
            badge.style.display = "none";
        }

        if (count >= 2) {
            compareBtn.disabled = false;
            selectionText.innerText = `${count} candidates selected for comparison.`;
        } else {
            compareBtn.disabled = true;
            selectionText.innerText = "Select 2 to 4 candidates to run comparative analysis.";
        }
    }

    // Run Comparison view loading
    document.getElementById("btn-run-comparison").onclick = async () => {
        if (selectedCandidateIds.length < 2) return;
        navigateTo("compare");
        window.location.hash = "compare";
        
        try {
            const surface = document.getElementById("compare-matrix-surface");
            surface.innerHTML = `<div style="text-align:center; padding: 40px;"><div class="spinner" style="margin: 0 auto 16px auto;"></div>Running comparative matrix algorithms...</div>`;
            
            const data = await API.compareCandidates(selectedCandidateIds);
            
            document.getElementById("compare-subtitle").innerText = `Side-by-Side comparison against: ${data.job_title}`;
            document.getElementById("compare-justification").innerHTML = `
                <strong>Why Candidate ranks higher:</strong>
                <p style="margin-top: 6px; font-style: italic;">${data.why_higher_justification}</p>
            `;
            
            surface.innerHTML = Components.renderComparisonMatrix(data);
            lucide.createIcons();
        } catch (e) {
            alert(e.message);
            window.location.hash = "candidates";
        }
    };

    // 4. Candidate Details Inspector
    async function showCandidateDetails(candId) {
        navigateTo("details");
        
        try {
            // Loading skeleton
            document.getElementById("prof-name").innerText = "Loading candidate Profile...";
            document.getElementById("prof-contact").innerText = "";
            document.getElementById("prof-timeline").innerHTML = `<div class="spinner" style="margin:20px;"></div>`;
            document.getElementById("table-prof-matrix").querySelector("tbody").innerHTML = "<tr><td colspan='4'>Retrieving details...</td></tr>";

            const candidate = await API.getCandidate(candId);
            
            // Get Match details. For the demo / simple database, we get the latest match matching this candidate ID
            const matches = allCandidates.filter(m => m.candidate_id.toString() === candId.toString());
            let match = matches[0];
            
            // If match not cached, retrieve fresh
            if (!match) {
                // Fetch screening runs and find match
                const runs = await API.getScreeningRuns();
                runs.forEach(r => {
                    r.matches.forEach(m => {
                        if (m.candidate_id.toString() === candId.toString()) {
                            match = m;
                        }
                    });
                });
            }

            if (!match) {
                alert("Match details not found for candidate.");
                window.location.hash = "candidates";
                return;
            }

            // Tabs behavior
            const btnTabIntelligence = document.getElementById("btn-tab-intelligence");
            const btnTabExtracted = document.getElementById("btn-tab-extracted");
            const panelTabIntelligence = document.getElementById("panel-tab-intelligence");
            const panelTabRaw = document.getElementById("panel-tab-raw");

            btnTabIntelligence.onclick = () => {
                btnTabIntelligence.classList.add("active");
                btnTabExtracted.classList.remove("active");
                panelTabIntelligence.style.display = "grid";
                panelTabRaw.style.display = "none";
            };

            btnTabExtracted.onclick = () => {
                btnTabExtracted.classList.add("active");
                btnTabIntelligence.classList.remove("active");
                panelTabIntelligence.style.display = "none";
                panelTabRaw.style.display = "flex";
            };

            // Reset tab navigation
            btnTabIntelligence.click();

            // Populate Raw JSON Panel
            const rawObj = {
                id: candidate.id,
                name: candidate.name,
                email: candidate.email,
                phone: candidate.phone,
                summary: candidate.summary,
                experience_years: candidate.experience_years,
                completeness_score: candidate.completeness_score,
                skills: candidate.candidate_skills.map(cs => ({
                    name: cs.skill.name,
                    years_experience: cs.years_experience,
                    evidence: cs.evidence_text
                })),
                experiences: candidate.experiences.map(exp => ({
                    company: exp.company,
                    role: exp.role,
                    start_date: exp.start_date,
                    end_date: exp.end_date,
                    description: exp.description,
                    years: exp.years
                })),
                educations: candidate.educations.map(edu => ({
                    institution: edu.institution,
                    degree: edu.degree,
                    field_of_study: edu.field_of_study,
                    start_date: edu.start_date,
                    end_date: edu.end_date
                })),
                projects: candidate.projects.map(proj => ({
                    title: proj.title,
                    description: proj.description,
                    technologies: proj.technologies
                })),
                timeline_issues: JSON.parse(candidate.timeline_issues || "[]")
            };
            document.getElementById("prof-raw-json").innerText = JSON.stringify(rawObj, null, 2);

            // Fill basic profile fields with Demo Badges if applicable
            const isDemo = ["John Doe", "Jane Smith", "Bob Jones", "Alice White", "Charlie Brown"].includes(candidate.name);
            if (isDemo) {
                document.getElementById("prof-name").innerHTML = `${candidate.name} <span class="badge badge-outline" style="font-size: 10px; color:#6B7280; border-color:#D1D5DB; font-weight:500; margin-left:8px; vertical-align:middle;">DEMO DATA</span>`;
            } else {
                document.getElementById("prof-name").innerText = candidate.name;
            }
            
            document.getElementById("prof-contact").innerText = `${candidate.email || "No email listed"} | ${candidate.phone || "No phone listed"}`;
            
            // Recommendation Badge
            const recBadge = document.getElementById("prof-rec-badge");
            recBadge.innerText = match.recommendation;
            recBadge.className = "badge";
            if (match.recommendation === "SHORTLIST") recBadge.classList.add("badge-success");
            else if (match.recommendation === "REVIEW") recBadge.classList.add("badge-warning");
            else if (match.recommendation === "NOT RECOMMENDED") recBadge.classList.add("badge-danger");

            document.getElementById("prof-completeness-badge").innerText = `Profile Completeness: ${Math.round(candidate.completeness_score)}%`;
            document.getElementById("prof-overall-score").innerText = Math.round(match.overall_score);
            document.getElementById("prof-summary").innerText = candidate.summary || "No professional summary available.";

            // Render Subcomponents
            document.getElementById("prof-timeline").innerHTML = Components.renderTimeline(candidate.experiences);
            document.getElementById("table-prof-matrix").querySelector("tbody").innerHTML = Components.renderRequirementsMatrix(match.match_requirements);
            document.getElementById("prof-score-breakdown").innerHTML = Components.renderScoreBreakdown(match);
            document.getElementById("timeline-warnings-list").innerHTML = Components.renderTimelineWarnings(candidate.timeline_issues);

            // Fetch Sensitivity Analysis
            const sensList = document.getElementById("prof-sensitivity-list");
            sensList.innerHTML = "Loading analysis...";
            
            try {
                const sensitivityData = await API.getMatchSensitivity(match.id);
                sensList.innerHTML = Components.renderSensitivityList(sensitivityData.potential_changes);
            } catch (err) {
                sensList.innerHTML = `<p class="quick-action-tip">Error loading sensitivity analysis.</p>`;
            }

            // Reinitialize vector icons inside details page
            lucide.createIcons();

        } catch (e) {
            console.error(e);
            alert("Error loading candidate profile.");
            window.location.hash = "candidates";
        }
    }

    document.getElementById("btn-back-to-candidates").onclick = () => {
        window.location.hash = "candidates";
    };

    // FORM & MODAL ACTIONS

    // Create Job Submission
    const jobForm = document.getElementById("form-create-job");
    jobForm.onsubmit = async (e) => {
        e.preventDefault();
        const title = document.getElementById("job-title").value;
        const dept = document.getElementById("job-dept").value;
        const desc = document.getElementById("job-desc").value;

        try {
            await API.createJob({
                title: title,
                department: dept,
                description: desc,
                requirements: [] // Auto-analyzed in backend
            });
            alert("Job role created and parsed successfully!");
            modals.job.style.display = "none";
            jobForm.reset();
            window.location.hash = "jobs";
            loadJobsData();
        } catch (err) {
            alert(err.message);
        }
    };

    // Populate Job Select in Upload Modal
    async function populateJobSelectDropdown() {
        const select = document.getElementById("upload-job-select");
        select.innerHTML = "";
        
        try {
            const jobs = await API.getJobs();
            if (jobs.length === 0) {
                select.innerHTML = `<option value="">-- Create a job first --</option>`;
                document.getElementById("btn-start-screening").disabled = true;
                return;
            }
            jobs.forEach(job => {
                select.innerHTML += `<option value="${job.id}">${job.title}</option>`;
            });
            document.getElementById("btn-start-screening").disabled = selectedFiles.length === 0;
        } catch (e) {
            console.error(e);
        }
    }

    // UPLOAD DRAG-AND-DROP FILE HANDLERS
    const dropzone = document.getElementById("dropzone-resumes");
    const fileInput = document.getElementById("file-input-resumes");
    const fileContainer = document.getElementById("selected-files-container");
    const fileListUl = document.getElementById("selected-files-list");
    const startScreeningBtn = document.getElementById("btn-start-screening");

    dropzone.onclick = () => fileInput.click();

    dropzone.ondragover = (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--color-primary)";
    };

    dropzone.ondragleave = () => {
        dropzone.style.borderColor = "var(--color-border)";
    };

    dropzone.ondrop = (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--color-border)";
        handleFilesSelection(e.dataTransfer.files);
    };

    fileInput.onchange = (e) => {
        handleFilesSelection(e.target.files);
    };

    function handleFilesSelection(filesList) {
        for (const file of filesList) {
            // Check file type and size
            if (file.size > 5 * 1024 * 1024) {
                alert(`File ${file.name} is too large. Max size is 5MB.`);
                continue;
            }
            selectedFiles.push(file);
        }
        renderSelectedFiles();
    }

    function renderSelectedFiles() {
        fileListUl.innerHTML = "";
        if (selectedFiles.length === 0) {
            fileContainer.style.display = "none";
            startScreeningBtn.disabled = true;
            return;
        }

        fileContainer.style.display = "block";
        selectedFiles.forEach((file, index) => {
            fileListUl.innerHTML += `
                <li>
                    <span>📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>
                    <button type="button" class="btn-close" style="font-size:16px;" onclick="removeSelectedFile(${index})">&times;</button>
                </li>
            `;
        });
        
        const jobId = document.getElementById("upload-job-select").value;
        startScreeningBtn.disabled = !jobId;
    }

    // Expose file removal globally for the inline close buttons
    window.removeSelectedFile = (idx) => {
        selectedFiles.splice(idx, 1);
        renderSelectedFiles();
    };

    function resetUploadModal() {
        modals.upload.style.display = "none";
        selectedFiles = [];
        renderSelectedFiles();
        document.getElementById("pipeline-processing-loader").style.display = "none";
        document.getElementById("btn-start-screening").style.display = "inline-flex";
    }

    // SCREEN RESUMES ACTION WITH LIVE PIPELINE
    startScreeningBtn.onclick = async () => {
        const jobId = document.getElementById("upload-job-select").value;
        if (!jobId || selectedFiles.length === 0) return;

        // Hide upload triggers, show processing pipeline progress
        document.getElementById("pipeline-processing-loader").style.display = "flex";
        startScreeningBtn.style.display = "none";

        // Reset stage highlights
        updatePipelineStage("stage-upload");

        try {
            // 1. Submit upload
            const run = await API.screenResumes(jobId, selectedFiles);
            
            // 2. Poll screening run until completed
            pollScreeningStatus(run.id);

        } catch (err) {
            alert(err.message);
            resetUploadModal();
        }
    };

    // Poll status helper
    async function pollScreeningStatus(runId) {
        let attempts = 0;
        
        const interval = setInterval(async () => {
            attempts++;
            try {
                const run = await API.getScreeningRun(runId);
                
                // Simulate progress timing matching the actual async background task
                if (attempts === 2) updatePipelineStage("stage-parse");
                if (attempts === 4) updatePipelineStage("stage-normalize");
                if (attempts === 6) updatePipelineStage("stage-match");
                if (attempts === 8) updatePipelineStage("stage-score");

                if (run.status === "completed") {
                    clearInterval(interval);
                    alert("Resume screening successfully completed!");
                    resetUploadModal();
                    window.location.hash = "candidates";
                    loadCandidatesData();
                } else if (run.status === "failed") {
                    clearInterval(interval);
                    alert("Screening run failed. Verify PDF content.");
                    resetUploadModal();
                }
            } catch (e) {
                clearInterval(interval);
                alert("Error checking screening run status.");
                resetUploadModal();
            }
        }, 1500);
    }

    function updatePipelineStage(stageId) {
        document.querySelectorAll(".pipeline-stage").forEach(el => {
            el.classList.remove("active");
        });
        const target = document.getElementById(stageId);
        if (target) target.classList.add("active");
    }

    // 2-MINUTE QUICK DEMO RUN
    document.getElementById("btn-quick-run-demo").onclick = async () => {
        try {
            const btn = document.getElementById("btn-quick-run-demo");
            btn.disabled = true;
            btn.innerText = "Running demo pipeline...";

            // 1. Create default Job Profile
            const defaultJob = {
                title: "Senior Backend Developer",
                department: "Engineering",
                description: "We are seeking a Senior Backend Developer to join our team. The ideal candidate has deep expertise in Python development, particularly with creating REST APIs using the FastAPI framework. You must be comfortable structuring databases using PostgreSQL and configuring EC2 and RDS instances on AWS. Docker containerization knowledge is preferred. A Bachelor's Degree in Computer Science and at least 3+ years of professional backend engineering experience is required."
            };

            const job = await API.createJob(defaultJob);

            // 2. Programmatically generate 5 synthetic txt files
            const files = [
                new File([
                    "John Doe\nEmail: john.doe@example.com\nPhone: +1 (555) 111-2222\n" +
                    "Summary: Experienced Python developer. Built REST APIs using FastAPI and PostgreSQL inside Docker container setups on AWS cloud. 4.5 years experience.\n" +
                    "Education: BS in Computer Science from Georgia Tech (2018-2022).\n" +
                    "Experience:\nTech Solutions Corp - Senior Software Engineer (2023-01 to Present)\nStartup Labs - Intern (2022-05 to 2022-12)\n" +
                    "Projects:\nSmart Inventory System: Created forecasts using python, PostgreSQL and docker."
                ], "john_doe_excellent.txt", { type: "text/plain" }),
                
                new File([
                    "Jane Smith\nEmail: jane.smith@example.com\nPhone: +1 (555) 222-3333\n" +
                    "Summary: Coder focused on Python backend code, FastAPI microservices, and Postgres database queries. Has Docker container experience but lacks AWS exposure.\n" +
                    "Education: BS in Software Engineering from University of Washington (2019-2023).\n" +
                    "Experience:\nInnovate Software Inc - Backend Engineer (2023-06 to Present)\n" +
                    "Projects:\nCollaborative Task Manager: Developed postgres database inside Docker container setup."
                ], "jane_smith_aws_gap.txt", { type: "text/plain" }),
                
                new File([
                    "Bob Jones\nEmail: bob.jones@example.com\nPhone: +1 (555) 333-4444\n" +
                    "Summary: IT support technician with basic python scripting skills. 1.2 years total experience. No FastAPI, database, or cloud infrastructure.\n" +
                    "Education: Associate Degree in Information Systems.\n" +
                    "Experience:\nLocal Agency - IT Tech (2024-01 to Present)\n"
                ], "bob_jones_weak.txt", { type: "text/plain" }),
                
                new File([
                    "Alice White\nEmail: alice.white@example.com\nPhone: +1 (555) 444-5555\n" +
                    "Summary: Python backend dev. Developed FastAPI and Postgres on AWS. Has 3.5 years experience. Timeline notes: Apex (2023-01 to 2024-06) and Global Systems (2023-06 to 2024-12).\n" +
                    "Education: BS in CS from Seattle University.\n" +
                    "Experience:\nApex Consulting - Software Engineer (2023-01 to 2024-06)\nGlobal Systems - Architect (2023-06 to 2024-12)\n"
                ], "alice_white_timeline_issue.txt", { type: "text/plain" }),
                
                new File([
                    "Charlie Brown\n" +
                    "Summary: Python enthusiast.\n" +
                    "Experience:\nBeta Labs - Developer (2.0 years experience)\n"
                ], "charlie_brown_incomplete.txt", { type: "text/plain" })
            ];

            // 3. Dispatch file screening
            const run = await API.screenResumes(job.id, files);
            
            // 4. Highlight modal loader
            populateJobSelectDropdown();
            modals.upload.style.display = "flex";
            document.getElementById("pipeline-processing-loader").style.display = "flex";
            startScreeningBtn.style.display = "none";
            updatePipelineStage("stage-upload");
            
            // Poll
            pollScreeningStatus(run.id);

            // Re-enable demo button in background
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="play" style="width:14px; height:14px; margin-right:6px; vertical-align:middle; display:inline-block;"></i>Run 2-Minute Demo Run';
                lucide.createIcons();
            }, 3000);

        } catch (err) {
            alert("Demo failed: " + err.message);
            const btn = document.getElementById("btn-quick-run-demo");
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="play" style="width:14px; height:14px; margin-right:6px; vertical-align:middle; display:inline-block;"></i>Run 2-Minute Demo Run';
            lucide.createIcons();
        }
    };

    // Initialize Lucide icons on boot
    lucide.createIcons();
});
