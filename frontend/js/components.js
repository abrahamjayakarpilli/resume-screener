// TalentLens AI UI Components

const Components = {
    // 1. Render chronological work history timeline
    renderTimeline(experiences) {
        if (!experiences || experiences.length === 0) {
            return `<p class="quick-action-tip">No work experience listed.</p>`;
        }
        
        // Sort experiences by start_date descending
        const sorted = [...experiences].sort((a, b) => {
            if (!a.start_date) return 1;
            if (!b.start_date) return -1;
            return b.start_date.localeCompare(a.start_date);
        });

        return sorted.map(exp => {
            const dateStr = `${exp.start_date || 'Unknown'} — ${exp.end_date || 'Present'}`;
            const yearsStr = exp.years ? `(${exp.years.toFixed(1)} yrs)` : '';
            return `
                <div class="timeline-item">
                    <div class="timeline-date">${dateStr} ${yearsStr}</div>
                    <div class="timeline-role">${exp.role}</div>
                    <div class="timeline-company">${exp.company}</div>
                    <div class="timeline-desc">${exp.description || ''}</div>
                </div>
            `;
        }).join("");
    },

    // 2. Render requirement-by-requirement status matrix
    renderRequirementsMatrix(matchRequirements) {
        if (!matchRequirements || matchRequirements.length === 0) {
            return `<tr><td colspan="4">No requirements evaluated.</td></tr>`;
        }

        return matchRequirements.map(mr => {
            // Recommendation badges class
            let statusClass = "badge-outline";
            let statusIcon = "UNKNOWN";
            if (mr.status === "MATCH") {
                statusClass = "badge-success";
                statusIcon = "✓ MATCH";
            } else if (mr.status === "PARTIAL") {
                statusClass = "badge-warning";
                statusIcon = "~ PARTIAL";
            } else if (mr.status === "MISSING" || mr.status === "NO EVIDENCE") {
                statusClass = "badge-no-evidence";
                statusIcon = "NO EVIDENCE";
            }

            let confClass = "badge-outline";
            if (mr.confidence === "HIGH") confClass = "badge-success";
            else if (mr.confidence === "MEDIUM") confClass = "badge-warning";
            
            const evidenceText = mr.evidence || "No evidence found in the submitted resume.";
            const sourceText = mr.source_section ? `Location: ${mr.source_section}` : "Location: Not specified";

            return `
                <tr>
                    <td class="matrix-req-text">${mr.requirement.requirement_text}</td>
                    <td><span class="badge ${statusClass}">${statusIcon}</span></td>
                    <td><span class="badge ${confClass}">${mr.confidence}</span></td>
                    <td>
                        <div class="matrix-evidence-text">"${evidenceText}"</div>
                        <div class="matrix-source">${sourceText}</div>
                    </td>
                </tr>
            `;
        }).join("");
    },

    // 3. Render candidate suitability scores breakdown progress bars
    renderScoreBreakdown(match) {
        const categories = [
            { label: "Technical Skills Alignment", val: match.technical_score, weight: 40 },
            { label: "Relevant Experience Years", val: match.experience_score, weight: 30 },
            { label: "Projects / Technical Evidence", val: match.projects_score, weight: 15 },
            { label: "Education Verification", val: match.education_score, weight: 10 },
            { label: "Other Suitability Factors", val: match.other_score, weight: 5 }
        ];

        return categories.map(cat => {
            return `
                <div class="breakdown-row">
                    <div class="breakdown-lbl">
                        <span>${cat.label} <small style="color: #9CA3AF;">(${cat.weight}%)</small></span>
                        <span>${cat.val || 0}%</span>
                    </div>
                    <div class="breakdown-bar-bg">
                        <div class="breakdown-bar-fill" style="width: ${cat.val || 0}%;"></div>
                    </div>
                </div>
            `;
        }).join("");
    },

    // 4. Render recruiter decision sensitivity items ("what changes the decision?")
    renderSensitivityList(sensitivityList) {
        if (!sensitivityList || sensitivityList.length === 0) {
            return `<p class="quick-action-tip">The candidate already satisfies all identified critical and high requirements. No adjustments needed.</p>`;
        }

        return sensitivityList.map(item => {
            return `
                <div class="sensitivity-item">
                    <div>
                        <h4>Verify '${item.requirement_text}'</h4>
                        <small style="color: #9CA3AF; font-size:10px;">Importance: ${item.importance} | Current: ${item.current_status}</small>
                    </div>
                    <span>+${item.score_delta} pts</span>
                </div>
            `;
        }).join("");
    },

    // 5. Render chronological overlap warnings
    renderTimelineWarnings(warningsJSON) {
        if (!warningsJSON) {
            return `
                <div class="timeline-ok-item">
                    <span>✓</span>
                    <div>
                        <strong>Timeline Consistent</strong>
                        <p style="font-size: 11px; margin-top:2px;">No overlapping professional employments or degrees detected in work history.</p>
                    </div>
                </div>
            `;
        }

        try {
            const warnings = JSON.parse(warningsJSON);
            if (!warnings || warnings.length === 0) {
                return `
                    <div class="timeline-ok-item">
                        <span>✓</span>
                        <div>
                            <strong>Timeline Consistent</strong>
                            <p style="font-size: 11px; margin-top:2px;">No overlapping professional employments or degrees detected in work history.</p>
                        </div>
                    </div>
                `;
            }

            return warnings.map(warn => {
                return `
                    <div class="timeline-warning-item">
                        <span>⚠️</span>
                        <div>
                            <strong>Potential Timeline Conflict</strong>
                            <p style="font-size: 11px; margin-top:2px;">${warn}</p>
                        </div>
                    </div>
                `;
            }).join("");
        } catch (e) {
            return `<p class="quick-action-tip">Error parsing timeline consistency status.</p>`;
        }
    },

    // 6. Side-by-side Candidate Comparison Grid matrix
    renderComparisonMatrix(compareData) {
        const { requirements, candidates } = compareData;
        
        // Headers
        const headerRow = `
            <tr>
                <th>Requirement Criteria</th>
                ${candidates.map(c => `<th>${c.name}</th>`).join("")}
            </tr>
        `;

        // Match Score Row
        const scoreRow = `
            <tr>
                <td><strong>Overall Match Score</strong></td>
                ${candidates.map(c => `<td><strong style="color: var(--color-primary); font-size:16px;">${c.overall_score}/100</strong></td>`).join("")}
            </tr>
        `;

        // Recommendation Row
        const recRow = `
            <tr>
                <td><strong>Recommendation</strong></td>
                ${candidates.map(c => {
                    let badgeClass = "badge-outline";
                    if (c.recommendation === "SHORTLIST") badgeClass = "badge-success";
                    else if (c.recommendation === "REVIEW") badgeClass = "badge-warning";
                    return `<td><span class="badge ${badgeClass}">${c.recommendation}</span></td>`;
                }).join("")}
            </tr>
        `;

        // Total Experience Row
        const expRow = `
            <tr>
                <td><strong>Professional Experience</strong></td>
                ${candidates.map(c => `<td>${c.experience_years.toFixed(1)} yrs</td>`).join("")}
            </tr>
        `;

        // Dynamic Requirement Rows
        const reqRows = requirements.map(req => {
            const cells = candidates.map(c => {
                const reqMatches = Array.isArray(c.req_matches) 
                    ? c.req_matches 
                    : (Array.isArray(c.requirement_matches) ? c.requirement_matches : []);
                const matchVal = reqMatches.find(m => m.requirement_id === req.id);
                const status = matchVal ? matchVal.status : "UNKNOWN";
                
                let icon = "UNKNOWN";
                let color = "color: var(--color-text-secondary);";
                if (status === "MATCH") {
                    icon = "✓";
                    color = "color: var(--color-success); font-weight: bold; font-size: 16px;";
                } else if (status === "PARTIAL") {
                    icon = "~";
                    color = "color: var(--color-warning); font-weight: bold; font-size: 16px;";
                } else if (status === "MISSING" || status === "NO EVIDENCE") {
                    icon = "—";
                    color = "color: var(--color-text-muted); font-weight: bold; font-size: 16px;";
                }
                
                const hoverText = (status === "MISSING" || status === "NO EVIDENCE") ? "No evidence found in the submitted resume." : status;
                return `<td style="${color}" title="${hoverText}">${icon}</td>`;
            }).join("");

            return `
                <tr>
                    <td>${req.requirement_text} <small style="color:#9CA3AF;">(${req.importance})</small></td>
                    ${cells}
                </tr>
            `;
        }).join("");

        // Top Strengths Row
        const strengthsRow = `
            <tr>
                <td><strong>Key Strengths</strong></td>
                ${candidates.map(c => `<td>${c.strengths.length > 0 ? c.strengths.join(", ") : 'None listed'}</td>`).join("")}
            </tr>
        `;

        // Top Gaps Row
        const gapsRow = `
            <tr>
                <td><strong>Primary Gaps</strong></td>
                ${candidates.map(c => `<td>${c.gaps.length > 0 ? c.gaps.join(", ") : 'None listed'}</td>`).join("")}
            </tr>
        `;

        return `
            <table class="comparison-table">
                <thead>${headerRow}</thead>
                <tbody>
                    ${scoreRow}
                    ${recRow}
                    ${expRow}
                    ${reqRows}
                    ${strengthsRow}
                    ${gapsRow}
                </tbody>
            </table>
        `;
    }
};
