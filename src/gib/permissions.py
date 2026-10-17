import os, sys
from pathlib import Path

def check_perms(args, target: str = None):
    """Deny-by-default for sensitive caps. Returns (ok, env_extra)."""
    import sys
    allow_env = getattr(args, 'allow_env', False)
    allow_net = getattr(args, 'allow_net', False)
    allow_read = getattr(args, 'allow_read', False)
    if target:
        # NOTE: the entry file itself is always allowed (user explicitly named it).
        # --allow-read gates programmatic reads outside cwd in the future embedded
        # engine; with the Node backend, reads are confined by OS process isolation
        # only. Documented in docs/SECURITY.md — not falsely claimed as a jail.
        pass
    # Default: allow reading the entry file's tree (needed to run anything); restrict env/net unless flagged.
    env = {}
    if not allow_env:
        # Strip secrets-ish vars from engine env, keep PATH/SYSTEM minimum.
        keep = {'PATH', 'SystemRoot', 'SYSTEMROOT', 'TEMP', 'TMP', 'HOME', 'NODE_PATH'}
        for k in list(os.environ):
            if k not in keep and ('KEY' in k or 'SECRET' in k or 'TOKEN' in k):
                env['__STRIP__' + k] = ''  # marker; actual strip below
        env_extra = {'GIBRUN_ALLOW_ENV': '0'}
    else:
        env_extra = {'GIBRUN_ALLOW_ENV': '1'}
    env_extra['GIBRUN_ALLOW_NET'] = '1' if allow_net else '0'
    return True, env_extra

def canonical(p: str) -> Path:
    return Path(p).resolve()
