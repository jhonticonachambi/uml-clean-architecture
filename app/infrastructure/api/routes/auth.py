# infrastructure/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from app.application.use_cases.usuario.registrar_usuario import RegistrarUsuarioUseCase, RegistrarUsuarioRequest
from app.application.use_cases.usuario.login_usuario import LoginUsuarioUseCase, LoginUsuarioRequest
from app.infrastructure.dependencies import (
    get_registrar_usuario_use_case,
    get_login_use_case
)

router = APIRouter(tags=["Autenticación"])

@router.post("/registrar")
async def registrar_usuario(
    email: str,
    nombre: str,
    password: str,
    use_case: RegistrarUsuarioUseCase = Depends(get_registrar_usuario_use_case)
):
    try:
        usuario = await use_case.execute(RegistrarUsuarioRequest(email, nombre, password))  # ✅ FIX
        return {"id": usuario.id, "email": usuario.email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    email: str,
    password: str,
    use_case: LoginUsuarioUseCase = Depends(get_login_use_case)
):
    token = await use_case.execute(LoginUsuarioRequest(email, password))  # ✅ FIX
    if not token:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"access_token": token}
