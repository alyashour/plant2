"""Measure checkpoint-loading VRAM in a fresh process, without CARLA. Written by Codex"""
import argparse
import gc
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', required=True)
parser.add_argument('--checkpoint', required=True)
parser.add_argument('--load', choices=['cpu', 'gpu'], default='cpu', help='Deserialize on CPU or GPU; the final model is always on GPU.')
args = parser.parse_args()
sys.path.insert(0, str(Path(args.project) / 'carla_garage'))
sys.path.insert(0, str(Path(args.project) / 'PlanT'))
import torch
from lit_module import LitHFLM

if not torch.cuda.is_available():
    raise SystemExit('CUDA is unavailable in this process. Run in your GPU-enabled terminal with CUDA_VISIBLE_DEVICES unset.')

torch.cuda.init()
torch.cuda.synchronize()
gc.collect()
torch.cuda.empty_cache()
baseline = torch.cuda.memory_allocated()
free, total = torch.cuda.mem_get_info()
torch.cuda.reset_peak_memory_stats()
print(f'GPU: {torch.cuda.get_device_name()}', flush=True)
print(f'Before load: {free / 2**30:.3f} GiB free of {total / 2**30:.3f} GiB', flush=True)
status = 'ok'
try:
    # Only use trusted checkpoints: this project stores Python configuration objects.
    net = LitHFLM.load_from_checkpoint(args.checkpoint, map_location='cpu' if args.load == 'cpu' else 'cuda', weights_only=False)
    net = net.to('cuda').eval()
    torch.cuda.synchronize()
    gc.collect()
    parameter_bytes = sum(p.numel() * p.element_size() for p in net.parameters())
    print(f'Model parameters: {parameter_bytes / 2**30:.3f} GiB', flush=True)
except torch.OutOfMemoryError as exc:
    status = 'out_of_memory'
    print(str(exc), flush=True)
finally:
    print(json.dumps({
        'status': status,
        'load_mode': args.load,
        'allocated_after_load_GiB': (torch.cuda.memory_allocated() - baseline) / 2**30,
        'peak_allocated_during_load_GiB': (torch.cuda.max_memory_allocated() - baseline) / 2**30,
        'reserved_after_load_GiB': torch.cuda.memory_reserved() / 2**30,
        'peak_reserved_during_load_GiB': torch.cuda.max_memory_reserved() / 2**30,
    }, indent=2), flush=True)
    print('Measures loading only. CUDA context, CARLA, visualization, and inference need additional memory.', flush=True)
if status != 'ok':
    raise SystemExit(1)
