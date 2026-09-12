"""Publicacao atomica de STL binario validado; nao certifica geometria imprimivel."""
import hashlib,math,os,struct,tempfile
from pathlib import Path

def valida_stl(path):
    path=Path(path)
    with path.open('rb') as f:
        header=f.read(84)
        if len(header)!=84:raise ValueError('STL incompleto.')
        count=struct.unpack('<I',header[80:])[0]
        if count==0 or path.stat().st_size!=84+50*count:raise ValueError('Tamanho/triangulos do STL invalido.')
        for _ in range(count):
            if not all(math.isfinite(x) for x in struct.unpack('<12fH',f.read(50))[:12]):raise ValueError('STL contem numero nao finito.')
    return dict(triangulos=count,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def publicar_stl(destino,escrever,sobrescrever=False):
    target=Path(destino).absolute()
    if target.exists() and not sobrescrever:raise FileExistsError('Destino existe; use outro nome ou autorize sobrescrever explicitamente.')
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.modelagem-',suffix='.stl',dir=target.parent);os.close(fd)
    try:
        escrever(tmp)
        evidence=valida_stl(tmp)
        if sobrescrever:os.replace(tmp,target)
        else:
            # No replace race: a concurrent destination is not overwritten.
            os.link(tmp,target)
        return dict(arquivo=str(target),**evidence)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
