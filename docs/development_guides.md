# Development Guides

## Adding New Config Fields
1. Add to `PushToTalkConfig` Pydantic model in [src/push_to_talk.py](../src/push_to_talk.py)
2. Add GUI control in appropriate [src/gui/](../src/gui/) section
3. Update `requires_component_reinitialization()` if needed
4. Add tests to [tests/test_config_gui.py](../tests/test_config_gui.py)

## Adding New Transcription Providers
1. Create new class inheriting from [src/transcription_base.py](../src/transcription_base.py)
2. Implement `transcribe()` method
3. Register provider in [src/transcriber_factory.py](../src/transcriber_factory.py)
4. Add configuration field and validation in `PushToTalkConfig`
5. Add GUI section in [src/gui/api_section.py](../src/gui/api_section.py)
6. Add tests to [tests/test_transcription_[provider].py](../tests/)
7. Update [README.md](../README.md) with new models and configuration

## Adding New Text Refinement Providers
1. Create new class inheriting from [src/text_refiner_base.py](../src/text_refiner_base.py)
2. Implement `refine()` and `set_glossary()` methods
3. Implement `_get_appropriate_prompt()` for dual-prompt support
4. Register provider in [src/text_refiner_factory.py](../src/text_refiner_factory.py)
5. Add configuration fields (`refinement_provider`, `refinement_model`, `[provider]_api_key`) to `PushToTalkConfig`
6. Add GUI sections in [src/gui/api_section.py](../src/gui/api_section.py)
7. Add tests to [tests/test_text_refiner.py](../tests/test_text_refiner.py)
8. Update [README.md](../README.md) with new models and configuration

## Modifying Audio Pipeline
- Components initialized in `_initialize_components()` - see [src/push_to_talk.py](../src/push_to_talk.py)
- Transcription runs in daemon threads (non-blocking)
- Temp file cleanup in `_process_recorded_audio()`
- Test with integration tests in [tests/](../tests/) using real audio fixtures

## Custom Glossary
- Stored in `PushToTalkConfig.custom_glossary` as `List[str]`
- GUI management in [src/gui/glossary_section.py](../src/gui/glossary_section.py)
- Prompt selection in base refiner classes (`TextRefinerBase`, `TextRefinerOpenAI`, `CerebrasTextRefiner`) via `_get_appropriate_prompt()`
- Prompts in [src/config/prompts.py](../src/config/prompts.py) with dual-prompt system for glossary vs. non-glossary modes
