from flask import request, jsonify
from flask_socketio import emit
from models import Score, Match, db, Team
from . import score_bp
from socket_instance import socketio
from flask_cors import cross_origin


def update_successor_match(successor_match_id, current_match_id, winning_team_id):
    """Advance winner to successor match"""
    try:
        successor_match = Match.query.get(successor_match_id)
        if not successor_match:
            return

        if successor_match.predecessor_1 == current_match_id:
            successor_match.team1_id = winning_team_id
        elif successor_match.predecessor_2 == current_match_id:
            successor_match.team2_id = winning_team_id

        if successor_match.team1_id and successor_match.team2_id:
            scores = [
                Score(
                    match_id=successor_match.id,
                    team_id=successor_match.team1_id,
                    score=0,
                    tournament_id=successor_match.tournament_id
                ),
                Score(
                    match_id=successor_match.id,
                    team_id=successor_match.team2_id,
                    score=0,
                    tournament_id=successor_match.tournament_id
                )
            ]
            db.session.bulk_save_objects(scores)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        raise e


@score_bp.route('/update-score', methods=['POST'])
def update_score():
    data = request.get_json()

    match_id = data.get('match_id')
    tournament_id = data.get('tournament_id')
    score_input = data.get('score')
    final = data.get('final', False)
    outcome = data.get('outcome', 'normal')  

    if not match_id or not tournament_id:
        return jsonify({"error": "match_id and tournament_id are required"}), 400

    match = Match.query.filter_by(id=match_id).first()
    if not match:
        return jsonify({"error": "Match not found"}), 404

    
    # ✅ WALKOVER / NON-SCORE OUTCOMES
    
    if outcome != "normal":
        winner_team_id = data.get("winner_team_id")
        if not winner_team_id:
            return jsonify({"error": "winner_team_id required for walkover"}), 400

        match.outcome = outcome
        match.is_final = True
        match.status = "completed"
        match.winner_team_id = winner_team_id

        if match.successor:
            update_successor_match(match.successor, match.id, winner_team_id)

        db.session.commit()

        return jsonify({
            "message": "Match completed via walkover",
            "match_id": match.id,
            "outcome": outcome,
            "winner_team_id": winner_team_id
        }), 200

    if not score_input:
        return jsonify({"error": "score is required for normal matches"}), 400

    try:
        team1_score, team2_score = map(int, score_input.split('-'))
    except ValueError:
        return jsonify({'error': 'Score format must be "X-Y"'}), 400

    team1_score_record = Score.query.filter_by(
        match_id=match_id,
        team_id=match.team1_id,
        tournament_id=tournament_id
    ).first()

    team2_score_record = Score.query.filter_by(
        match_id=match_id,
        team_id=match.team2_id,
        tournament_id=tournament_id
    ).first()

    if not team1_score_record:
        team1_score_record = Score(
            match_id=match_id,
            team_id=match.team1_id,
            tournament_id=tournament_id,
            score=team1_score
        )
        db.session.add(team1_score_record)
    else:
        team1_score_record.score = team1_score

    if not team2_score_record:
        team2_score_record = Score(
            match_id=match_id,
            team_id=match.team2_id,
            tournament_id=tournament_id,
            score=team2_score
        )
        db.session.add(team2_score_record)
    else:
        team2_score_record.score = team2_score

    if final:
        match.is_final = True
        match.outcome = "normal"

        if team1_score > team2_score:
            match.winner_team_id = match.team1_id
        elif team2_score > team1_score:
            match.winner_team_id = match.team2_id
        else:
            match.winner_team_id = None

        if match.successor and match.winner_team_id:
            update_successor_match(match.successor, match.id, match.winner_team_id)

    db.session.commit()

    response = {
        "message": "Scores updated successfully",
        "match_id": match.id,
        "team1_score": team1_score,
        "team2_score": team2_score,
        "winner_team_id": match.winner_team_id,
        "is_final": match.is_final
    }

    socketio.emit('score_update', response, namespace='/scores')

    return jsonify(response), 200
