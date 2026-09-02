from app.services.llm_label_service import build_scene_prompt, parse_llm_annotations


def test_parse_llm_annotations_normalizes_platform_shape():
    result = parse_llm_annotations(
        '```json\n{"objects":[{"label":"未戴安全帽人员","bbox":[0.1,0.2,0.8,0.9],"confidence":0.93}]}\n```',
        0.5,
    )
    assert len(result) == 1
    assert result[0]['label'] == '未戴安全帽人员'
    assert result[0]['source'] == 'llm-harness'
    assert result[0]['points'][2] == {'x': 0.8, 'y': 0.9}


def test_parse_llm_annotations_filters_invalid_and_low_confidence():
    result = parse_llm_annotations(
        '{"objects":[{"label":"人员","bbox":[0,0,1,1],"confidence":0.2},'
        '{"label":"错误框","bbox":[0.8,0.8,0.2,0.2],"confidence":0.9}]}',
        0.5,
    )
    assert result == []


def test_scene_prompt_keeps_rich_natural_language():
    scene = '只标注车间作业区内未戴安全帽的人员，排除海报和屏幕中的人物。'
    prompt = build_scene_prompt(scene, ['未戴安全帽人员'])
    assert scene in prompt
    assert '未戴安全帽人员' in prompt
    assert '归一化坐标' in prompt
