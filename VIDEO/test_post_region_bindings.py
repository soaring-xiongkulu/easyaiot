"""Persist and migrate geometry/plugin relationships with real SQLite queries."""
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from test_post_business_results import module, config, results

service=module('bindings','app/services/post_region_binding_service.py')
Base=declarative_base()


class Task(Base):
    __tablename__='task'
    id=Column(Integer,primary_key=True)
    post_pipeline=Column(String)
    template_revision=Column(Integer,default=1)
    task_type=Column(String,default='realtime')
    executor=Column(String,default='python')
    tracking_enabled=Column(Boolean,default=True)
    alert_event_enabled=Column(Boolean,default=True)
    updated_at=Column(DateTime)


class Region(Base):
    __tablename__='region'
    id=Column(Integer,primary_key=True)
    task_id=Column(Integer)
    device_id=Column(String)
    region_type=Column(String)
    region_name=Column(String)
    is_enabled=Column(Boolean,default=True)


class Conflict(ValueError):
    pass


class BindingTest(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.session=sessionmaker(bind=self.engine)()
        Task.query=self.session.query(Task);Region.query=self.session.query(Region)
        self.session.add(Task(id=1,post_pipeline=json.dumps([
            {'plugin':'region_gate'}, {'plugin':'line_cross','params':{'direction':'forward','target_classes':['person']}}, {'plugin':'default_pass'}])))
        self.session.add_all([Region(id=1,task_id=1,device_id='a',region_type='line',region_name='正门'),Region(id=2,task_id=1,device_id='b',region_type='line',region_name='后门'),Region(id=3,task_id=1,device_id='a',region_type='polygon',region_name='大厅'),Region(id=4,task_id=99,device_id='x',region_type='line')])
        self.session.commit()
        self.modules=patch.dict(sys.modules,{'models':SimpleNamespace(db=SimpleNamespace(session=self.session),AlgorithmTask=Task,DeviceDetectionRegion=Region), 'app.utils.region_hit_mode':config,'app.services.device_detection_region_service':SimpleNamespace(RegionRevisionConflict=Conflict)})
        self.modules.start()

    def tearDown(self):
        self.modules.stop();self.session.close();self.engine.dispose()

    def test_migration_preserves_other_camera_and_parameters(self):
        state=service.save_binding(1,1,{'expected_revision':1,'plugin':'line_cross','params':{'direction':'both'}})
        self.assertEqual(2,state['revision'])
        self.assertEqual([],state['legacy_plugins'])
        rules=[s for s in state['pipeline'] if s['plugin']=='line_cross']
        self.assertEqual(2,len(rules))
        other=next(s for s in rules if s['params']['region_ids']==[2])
        self.assertEqual('forward',other['params']['direction'])
        with self.assertRaises(Conflict):
            service.save_binding(1,1,{'expected_revision':1,'plugin':'line_cross'})

    def test_rejects_foreign_region_and_wrong_geometry(self):
        for rid,plugin in [(4,'line_cross'),(3,'line_cross'),(1,'dwell_timer')]:
            with self.assertRaises(ValueError):
                service.save_binding(1,rid,{'expected_revision':1,'plugin':plugin})

    def test_remove_only_selected_binding(self):
        state=service.save_binding(1,1,{'expected_revision':1,'plugin':'line_cross','remove':True})
        rules=[s for s in state['pipeline'] if s['plugin']=='line_cross']
        self.assertEqual([[2]],[s['params']['region_ids'] for s in rules])

    def test_statistics_for_each_bound_shape(self):
        info={'enrichment':{'business_rules':[
            {'plugin':'line_cross','region_id':1,'result':{'crossed':[{'region_id':1,'direction':'forward'}]}},
            {'plugin':'line_cross','region_id':2,'result':{'crossed':[{'region_id':2,'direction':'backward'}]}},
        ]}}
        self.assertEqual(2,len(results.business_results(info)['line_cross']['crossed']))
        self.assertEqual('forward',results.business_results(info,1)['line_cross']['crossed'][0]['direction'])
        self.assertEqual({},results.business_results(info,999))


if __name__=='__main__':
    unittest.main()
