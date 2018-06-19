from flask import Blueprint, jsonify, g

from http_quiz.product_quiz.translations import _
from http_quiz.quiz.quiz import candidate_token_required
from http_quiz.quiz.repo import QuizRepo

products_view = Blueprint('product_quiz', __name__)


@products_view.route('/product_quiz/')
def root():
    data = {'message': 'You are at the root of all the endpoints. Please go to /product_quiz/problem_statement/ '
                       'for the first problem'}
    return jsonify(data), 200


welcome_message = _('Welcome to the  product quiz.')
this_stage_number_is = _('This problem number is {0}.')
problem_statement = [
    _('Compute the count for the total number of products in the list given via input'),
    _('Active products are those for which current date time fall within start and end date of the current date. '
      'Compute the count of all such products')
]
the_input_output_url_is = _(
    'The input url for getting the test data is GET on /product/{0}/input/ and the data will '
    'be in JSON. And you will have to respond with the output on the URL by doing a POST on /product_quiz/{0}/output/.'
)
example_included_here = _('The examples for the sample input and output are included here.')

first_problem = {
    'message': ' '.join((
        welcome_message,
        this_stage_number_is.format(1),
        problem_statement[0],
        the_input_output_url_is.format(1),
        example_included_here,
    )),
    'example': {
        'input': {
            'end_date': '',
        },
        'output': {
            'end_date': '',
        }
    }
}

second_problem = {
    'message': ' '.join((
        this_stage_number_is.format(2),
        problem_statement[1],
        the_input_output_url_is.format(2),
        example_included_here,
    )),
    'example': {
        'input': {
            'end_date': '',
        },
        'output': {
            'end_date': '',
        }
    }
}


@products_view.route('/product_quiz/problem_statement', methods=('GET',))
@candidate_token_required('sequential', 'product')
def problem_statement():
    if QuizRepo.fetch_latest_answer_by_candidate(g.candidate) in (0, None):
        return jsonify({'message': first_problem['message']}), 200
    data = {'message': ''}
    return jsonify(data), 200


@products_view.route('/product_quiz/<int:problem_number>/input', methods=('GET',))
@candidate_token_required('sequential', 'product')
def problem_input(problem_number):
    input_ = {}
    output = {}
    if QuizRepo.fetch_latest_answer_by_candidate(g.candidate) in (0, None):
        QuizRepo.add_or_update_problem_input_output(input_, output, g.candidate, problem_number)
        return jsonify(input_)


@products_view.route('/product_quiz/<int:problem_number>/output', methods=('POST',))
@candidate_token_required('sequential', 'product')
def problem_output(problem_number):
    pass
