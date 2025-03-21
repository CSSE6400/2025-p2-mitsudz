from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

@api.route('/todos', methods=['GET'])
def get_todos():
    """Return the list of todo items"""
    # Error check request:
    completed = request.args.get('completed', None)
    comp_map = {'true': True, 'false': False}
    if completed is not None:
        if completed.lower() not in comp_map:
            return jsonify({'error' : 'completed must be a boolean'}), 400
        completed = comp_map[completed.lower()]

    window = request.args.get('window', None)
    if window is not None:
        try: window = int(window)
        except ValueError: return jsonify({'error' : 'window must be an integer'}), 400

    # Filter todos
    todos = Todo.query.all()
    result = []
    for todo in todos:
        # Check completion status
        if completed is not None and todo.completed != completed:
            continue
        # Check deadline window
        if window is not None:
            if todo.deadline_at is None: continue
            if (todo.deadline_at - datetime.utcnow()).days > window: continue
        
        # Add to return values
        result.append(todo.to_dict())

    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Return the details of a todo item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error' : 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo item and return the created item"""
    # Error checking request:
    alllowed = {'title', 'description', 'completed', 'deadline_at'}
    if len(set(request.json.keys()) - alllowed) > 0:
        return jsonify({'error' : 'Invalid keys'}), 400
    if 'title' not in request.json:
        return jsonify({'error' : 'title is required'}), 400

    # Create todo:
    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json['deadline_at'])

    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo item and return the updated item"""
    allowed = {'title', 'description', 'completed', 'deadline_at'}
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error' : 'Todo not found'}), 404
    
    if len(set(request.json.keys()) - allowed) > 0:
        return jsonify({'error' : "created_at and updated_at cannot be updated"}), 400
    
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()

    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo item and return the deleted item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return '', 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict())
 
