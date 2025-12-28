| **# Pools** | **Same-Pool Pairing**                        | **Near-pool Pairing**                       | **Half-Pool Pairing**                     | **Far-Pool Pairing**                     |
|-------------|----------------------------------------------|---------------------------------------------|-------------------------------------------|------------------------------------------|
| **2 Pools** | A1 vs A2, B1 vs B2                           | A1 vs B2, A2 vs B1                         | A1 vs A2, B1 vs B2 (same as "same-pool")  | A1 vs B2, A2 vs B1                       |
| **4 Pools** | A1 vs A2, B1 vs B2, C1 vs C2, D1 vs D2       | A1 vs B2, A2 vs B1, C1 vs D2, C2 vs D1     | A1 vs B2, A2 vs B1, C1 vs D2, C2 vs D1    | A1 vs D2, A2 vs D1, B1 vs C2, B2 vs C1   |
| **8 Pools** | A1 vs A2, B1 vs B2, C1 vs C2, D1 vs D2, E1 vs E2, F1 vs F2, G1 vs G2, H1 vs H2 | A1 vs B2, A2 vs B1, C1 vs D2, C2 vs D1, E1 vs F2, E2 vs F1, G1 vs H2, G2 vs H1 | A1 vs D2, A2 vs D1, E1 vs H2, H1 vs E2    | A1 vs H2, A2 vs H1, B1 vs G2, B2 vs G1, C1 vs F2, C2 vs F1, D1 vs E2, D2 vs E1 |


Overview

=> This project extends the existing v0 Khel Club tournament management system to support a new match outcome: Walkover.

    The original system only supported matches where both teams played and scores were entered numerically. The goal of this assignment was to understand the existing architecture and scoring flow, and then introduce Walkover support in a way that is clean, scalable, and future-proof, without breaking any existing behavior.

    While implementing Walkover, I focused on:

    Understanding how matches, scores, and brackets currently work
    Keeping scoring logic intact for normal matches
    Separating match outcome from score calculation
    Making it easy to add future outcomes like forfeit or bye
    Understanding the Existing System


High-Level Architecture

=> The system consists of:

    Backend: Flask + SQLAlchemy + MySQL

    Frontend: Next.js (v0 UI)

    Database: Relational schema for tournaments, teams, matches, scores

    Matches are connected in a bracket structure using:

    predecessor_1

    predecessor_2

    successor

    When a match is finalized, the winner automatically advances to the next match.

    Existing Scoring Mechanism (Before Changes)

    Before Walkover support, the flow was:

    A match is created with two teams

    Scores are submitted via the /update-score API

    Format: "score": "11-7"

    When final=true is passed:

    The match is marked final

    The winner is decided by comparing numeric scores

    The winner is propagated to the successor match

    Score records are created for both teams

Important limitation:
=> All logic assumed a numeric score. There was no way to represent a match where one team did not play at all (walkover).

    Design Goals for Walkover Support

    Before writing code, I defined a few constraints:
    Walkover should not require fake scores like 11-0
    Normal scoring behavior should remain unchanged
    Match result logic should be centralized in the backend
    The solution should support future match outcomes

Frontend changes should be minimal and reuse existing UI

What I Changed (Backend)
1. Introduced Match Outcome

I added a new concept called Match Outcome, separate from score values.

class MatchOutcome(str, Enum):
    NORMAL = "normal"
    WALKOVER = "walkover"
    FORFEIT = "forfeit"


This allows the system to represent how a match ended, not just what the score was.

2. Schema Change (Match Table)

I added a new column to the Match model:

outcome = db.Column(db.String(20), default="normal")


Existing matches default to normal

Walkover matches explicitly store walkover

This avoids hard-coding logic based on scores

No existing behavior is affected by this change.

3. Centralized Match Finalization Logic

Instead of tying match completion only to numeric scores, the backend now supports:

Normal match

Scores are required

Winner is determined by comparing scores

Walkover match

No scores are required

Winner is explicitly provided

Match is finalized immediately

Winner advances in the bracket

This keeps scoring logic and outcome logic separate.

4. API Extension (Non-Breaking)

The existing /update-score API continues to work as-is for normal matches.

For walkovers:

The match outcome is set to "walkover"

winner_team_id is set directly

Score creation is skipped

Successor match is still updated correctly

No existing frontend or API consumers break due to this change.

What I Changed (Frontend)
Displaying Walkover Matches

On the frontend:

Matches with outcome = "walkover" are clearly labeled

A visible “Walkover” indicator is shown

The winning team is still clearly communicated

Existing match and bracket components are reused

No UI redesign was required.

Why This Approach Is Scalable

This solution makes it easy to add new match outcomes in the future:

Add a new value to MatchOutcome

Handle it in the centralized match finalization logic

Optionally add a UI label

No schema redesign or major refactors are required.

Examples of future outcomes:

Forfeit

Bye

Disqualification

Assumptions Made

A walkover always has a clear winner

Walkover matches should advance winners in the bracket

Walkover matches do not require score records

Existing tournament data should continue to work unchanged

What I Would Improve With More Time

Add explicit backend validation for allowed outcome transitions

Add admin UI controls to mark a match as walkover

Add automated tests for match outcome logic

Improve frontend error handling around match finalization

How to Run the Project
Backend
cd v0_backend
python app.py

Frontend
cd v0_frontend
npm install --legacy-peer-deps
npm run dev



Known Limitations

    Some frontend-referenced APIs are not implemented in this backend
    CORS issues may occur due to missing routes
    These are known issues in the provided v0 repository