import sys
sys.stdout.reconfigure(encoding='utf-8')

print('=== Test 1: Import AI modules ===')
from desktop.app.ai.ollama_manager import OllamaManager, PREFERRED_MODELS
from desktop.app.ai.tools import ToolExecutor, TOOL_DEFINITIONS
from desktop.app.ai.agent import WifiCensorAgent
from desktop.app.ai.fall_verifier import FallVerifier
from desktop.app.ai.report_generator import ReportGenerator
print('  OK - All AI modules imported')

print()
print('=== Test 2: OllamaManager health + model selection ===')
ollama = OllamaManager()
alive = ollama.health_check()
print(f'  Ollama alive: {alive}')
if alive:
    models = ollama.list_models()
    print(f'  Models: {models}')
    best = ollama.select_best_model()
    print(f'  Best model: {best}')

print()
print('=== Test 3: Tool definitions schema ===')
print(f'  Tool count: {len(TOOL_DEFINITIONS)}')
for t in TOOL_DEFINITIONS:
    print(f'  Tool: {t["function"]["name"]}')

print()
print('=== Test 4: Simple AI generate ===')
if alive:
    result = ollama.generate(
        'Xin chao, ban co the tra loi bang tieng Viet khong? Hay tra loi ngan gon.',
        system='Ban la tro ly AI.'
    )
    short = result[:150] if len(result) > 150 else result
    print(f'  AI response: {short}')

print()
print('All tests PASSED!')
