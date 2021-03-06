import re
from types import MethodType

import pytest
from flask import json
from flask.testing import FlaskClient

from app import app
from http_quest.ext import db, mail
from http_quest.quiz.model import QuizType
from http_quest.quiz.repo import CandidateRepo
from http_quest.user.model import User
from http_quest.user.repo import UserRepo
from http_quest.user.user import create_user


def _post_json(self, url: str = '/', body=None, headers=None):
    headers = {} if headers is None else headers
    body = {} if body is None else body
    return self.post(
        url,
        data=json.dumps(body),
        content_type='application/json',
        headers=headers,
    )


class DatabaseTest:
    def new_user(self, email: str = None, password: str = None):
        return User(
            email=email or 'user@domain.com',
            password=(password or b'password'.decode()),
        )

    @pytest.fixture(autouse=True)
    def database_setup(self):
        self._ctx = app.test_request_context()
        self._ctx.push()
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield
        if hasattr(self, '_ctx'):
            self._ctx.pop()


class ApiTestBase(DatabaseTest):
    def create_user(self):
        create_user('user@domain.com', 'password')
        self.mail_outbox.pop()
        return UserRepo.fetch_user_by_email('user@domain.com')

    @staticmethod
    def sample_quiz_creation_body(quiz_type=str(QuizType.SEQUENTIAL), quiz_name='product'):
        return {
            'email': 'candidate@domain.com',
            'name': 'Jane Doe',
            'quiz_type': quiz_type,
            'quiz_name': quiz_name,
        }

    def create_candidate(self, quiz_type=str(QuizType.SEQUENTIAL), quiz_name='product') -> str:
        user = self.create_user()
        token = self.request_login_token(self.app_test, user)
        body = self.sample_quiz_creation_body(quiz_type=quiz_type, quiz_name=quiz_name)
        headers = {'Authorization': token}
        self.app_test.post_json(url='/quiz/new_candidate_token', body=body, headers=headers)
        candidate_token = self.mail_body_extract_token()
        self.candidate = CandidateRepo.fetch_candidate_by_token(candidate_token)
        return candidate_token

    @staticmethod
    def create_app() -> FlaskClient:
        mail.init_app(app)
        with app.app_context():
            return app.test_client()

    @pytest.fixture
    def mail_outbox(self):
        with mail.record_messages() as outbox:
            yield outbox

    @pytest.fixture(autouse=True)
    def api_setup(self, mail_outbox):
        self.app_test = self.create_app()
        self.mail_outbox = mail_outbox
        self.app_test.post()
        self.app_test.post_json = MethodType(_post_json, self.app_test)

    @staticmethod
    def request_login(app_test, user: User, password: str = None):
        request_payload = {'email': user.email, 'password': 'password' if password is None else password}
        response = app_test.post_json(url='/user/login', body=request_payload)
        return response

    @staticmethod
    def request_login_token(app_test, user: User) -> str:
        response = ApiTestBase.request_login(app_test, user)
        token = 'JWT ' + json.loads(response.data)['access_token']
        return token

    @staticmethod
    def assert_response_ok_and_has_message(response):
        assert response.status_code == 200
        assert 'message' in json.loads(response.data)

    def mail_body_json(self) -> dict:
        return json.loads(self.mail_outbox[0].body.replace("'", '"'))

    def mail_body_extract_token(self) -> str:
        uuid_pattern = re.compile(r'([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})')
        match = uuid_pattern.search(self.mail_outbox[0].body)
        return match.string[match.start():match.end()]

    def assert_has_one_mail_with_subject(self, subject):
        assert len(self.mail_outbox) == 1
        assert self.mail_outbox[0].subject == subject

    def assert_has_one_mail_with_subject_and_recipients(self, subject, recipients):
        self.assert_has_one_mail_with_subject(subject)
        assert set(self.mail_outbox[0].recipients) == set(recipients)
