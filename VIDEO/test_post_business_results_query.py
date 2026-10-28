"""Execute business-result queries against SQLite, including task/camera isolation."""
import json
import sys
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from test_post_business_results import results

Base = declarative_base()


class Alert(Base):
    __tablename__ = 'alert'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    time = Column(DateTime(timezone=True))
    device_id = Column(String)
    device_name = Column(String)
    region = Column(String)
    information = Column(String)


class ResultQueryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        Alert.query = self.session.query(Alert)
        for index, task, device in [(1, 1, 'a'), (2, 1, 'b'), (3, 2, 'a')]:
            self.session.add(Alert(id=index, task_id=task, device_id=device, time=datetime(2026, 10, 28, 1, tzinfo=timezone.utc),
                information=json.dumps({'enrichment': {'line_cross': {'crossed': [{'direction': 'forward'}]}}})))
        self.session.add(Alert(id=4, task_id=1, device_id='a', time=datetime(2026, 10, 28, 1), information='bad json'))
        self.session.commit()
        self.args = {'start': '2026-10-28T00:00:00+08:00', 'end': '2026-10-29T00:00:00+08:00', 'page_size': '1'}
        self.models = patch.dict(sys.modules, {'models': SimpleNamespace(Alert=Alert)})
        self.models.start()

    def tearDown(self):
        self.models.stop()
        self.session.close()
        self.engine.dispose()

    def test_pagination_summary_and_task_isolation(self):
        data = results.list_business_results(1, self.args)
        self.assertEqual(2, data['total'])
        self.assertEqual(2, data['summary']['crossings'])
        self.assertEqual([2], [item['id'] for item in data['items']])
        data = results.list_business_results(1, {**self.args, 'page': '2'})
        self.assertEqual([1], [item['id'] for item in data['items']])

    def test_camera_and_plugin_filters(self):
        data = results.list_business_results(1, {**self.args, 'device_id': 'a'})
        self.assertEqual(1, data['total'])
        data = results.list_business_results(1, {**self.args, 'plugin': 'dwell_timer'})
        self.assertEqual(0, data['total'])

    def test_invalid_ranges_and_pagination(self):
        for args in ({'page': '0'}, {'page_size': '101'}, {'start': '2026-10-28'}, {'end': '2027-01-01T00:00:00Z'}):
            with self.assertRaises(ValueError):
                results.list_business_results(1, {**self.args, **args})

    def test_local_day_includes_previous_utc_evening(self):
        self.session.add(Alert(id=5, task_id=1, device_id='c', time=datetime(2026, 10, 27, 17),
            information=json.dumps({'enrichment': {'headcount_gate': {'count': 7}}})))
        self.session.commit()
        data = results.list_business_results(1, {**self.args, 'device_id': 'c'})
        self.assertEqual(1, data['total'])
        self.assertEqual(7, data['summary']['peak_count'])
        self.assertTrue(data['items'][0]['time'].endswith('+00:00'))


if __name__ == '__main__':
    unittest.main()
