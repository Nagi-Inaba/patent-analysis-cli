from types import MappingProxyType

from patent_analysis import advanced_presentation as presentation


def test_registering_a_presentation_does_not_activate_an_unbuilt_mark(monkeypatch):
    future = presentation.AdvancedPresentation(
        'unbuilt-native.v1', 'unbuilt-native-svg.v1', 'network',
        'Synthetic unbuilt mark', 'inventor-network',
    )
    monkeypatch.setattr(presentation, 'ADVANCED_PRESENTATIONS', MappingProxyType({
        **presentation.ADVANCED_PRESENTATIONS, future.analysis_id: future,
    }))
    assert presentation.ADVANCED_BUILD is not None
    assert presentation.advanced_marks_for(future.analysis_id) == ()


def test_generated_built_mark_inventory_is_authoritative(monkeypatch):
    identity = 'inventor-tracking.v1'
    monkeypatch.setattr(presentation, 'ADVANCED_BUILD', {'built_marks': []})
    assert presentation.advanced_marks_for(identity) == ()
    monkeypatch.setattr(presentation, 'ADVANCED_BUILD', {
        'built_marks': ['inventor-tracking-svg.v1'],
    })
    assert presentation.advanced_marks_for(identity) == ('inventor-tracking-svg.v1',)
