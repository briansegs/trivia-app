import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginated_questions(request, questions_list):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    formatted_questions = [question.format() for question in questions_list]
    paginated_questions = formatted_questions[start:end]
    return paginated_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
          'Access-Control-Allow-Headers',
          'Content-Type,Authorization,true'
          )
        response.headers.add(
          'Access-Control-Allow-Methods',
          'GET,PATCH,POST,DELETE,OPTIONS'
          )
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        if categories is None:
            abort(404)

        formatted_categories = {
          category.id: category.type for category in categories
          }

        return jsonify({
          'success': True,
          'categories': formatted_categories
        })

    @app.route('/questions/')
    def get_questions():
        questions_list = Question.query.order_by(Question.id).all()
        ordered_questions = paginated_questions(request, questions_list)

        formatted_categories = {
          category.id: category.type for category in Category.query.all()
          }

        if len(ordered_questions) == 0:
            abort(404)

        return jsonify({
          'success': True,
          'questions': ordered_questions,
          'total_questions': len(questions_list),
          'current_category': None,
          'categories': formatted_categories
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = (
              Question.query.filter(Question.id == question_id).one_or_none()
            )

            if question is None:
                abort(422)

            question.delete()
            questions_list = Question.query.order_by(Question.id).all()
            ordered_questions = paginated_questions(request, questions_list)

            return jsonify({
              'success': True,
              'deleted': question_id,
              'questions': ordered_questions,
              'total_questions': len(questions_list),
            })

        except Exception:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')

        if new_question == '' or new_answer == '':
            abort(400)

        try:
            question = Question(
              question=new_question,
              answer=new_answer,
              category=new_category,
              difficulty=new_difficulty
            )

            question.insert()

            return jsonify({
              'success': True,
              'created': question.id
            })

        except Exception:
            abort(422)

    @app.route('/questions/search/', methods=['POST'])
    def search_questions():
        body = request.get_json()
        word = body['searchTerm'].lower()
        questions_list = []

        for question in Question.query.order_by(Question.id).all():
            if word in question.question.lower():
                questions_list.append(question)

        ordered_questions = paginated_questions(request, questions_list)

        formatted_categories = {
          category.id: category.type for category in Category.query.all()
          }

        if len(ordered_questions) == 0:
            abort(404)

        return jsonify({
          'success': True,
          'questions': ordered_questions,
          'total_questions': len(questions_list),
          'current_category': None,
          'categories': formatted_categories
        })

    @app.route('/categories/<int:category_id>/questions')
    def get_question_by_category(category_id):
        questions_list = []

        for question in Question.query.order_by(Question.id).all():
            if category_id == question.category:
                questions_list.append(question)

        ordered_questions = paginated_questions(request, questions_list)

        formatted_categories = {
          category.id: category.type for category in Category.query.all()
          }

        return jsonify({
          'success': True,
          'questions': ordered_questions,
          'total_questions': len(questions_list),
          'current_category': None,
          'categories': formatted_categories
        })

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        body = request.get_json()
        quiz_category = body['quiz_category']['id']
        previous_questions = body['previous_questions']
        questions = []

        if quiz_category == 0:
            questions_list = Question.query.all()
        else:
            questions_list = (
              Question.query.filter(Question.category == quiz_category).all()
            )

        for question in questions_list:
            if question.id not in previous_questions:
                questions.append(question)

        current_questions = [question.format() for question in questions]

        if len(current_questions) == 0:
            question = False
        else:
            question = random.choice(current_questions)

        return jsonify({
          'success': True,
          'question': question
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
          'success': False,
          'error': 404,
          'message': 'Resource Not Found'
        }), 404

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
          'success': False,
          'error': 405,
          'message': 'Method Not Allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
          'success': False,
          'error': 422,
          'message': 'Unprocessable Entity'
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
          'success': False,
          'error': 400,
          'message': 'Bad Request'
        }), 400

    return app
