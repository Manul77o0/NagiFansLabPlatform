from pydantic import BaseModel, Field


# FOR AUTH
class Token(BaseModel):
    access_token: str
    token_type: str


class BrowserLogin(BaseModel):
    username: str
    password: str


class InitialAdminRequest(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    password: str = Field(min_length=12, max_length=256)
    setup_token: str = Field(min_length=32, max_length=256)


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    id: int
    displayname: str
    email: str | None = None
    level: int | None = 0
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str | None = None


class UpdateUserRequest(BaseModel):
    displayName: str


class UpdateUserLevelRequest(BaseModel):
    level: int = Field(strict=True, ge=1, le=3)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class Result(BaseModel):
    result: str


class Tools(BaseModel):
    tools: list


# FOR WG_TOOLS
class WGGlobal(BaseModel):
    Endpoint: str
    DNSServer: str
    MTU: int
    PersistentKeepalive: int
    FirewallMark: str | None = "0xca6c"
    Table: str | None = "auto"


class WGServer(BaseModel):
    ServerInterface: str
    ListenPort: int
    Address: str | None = None
    PostUpScript: str | None = None
    PreDownScript: str | None = None
    PostDownScript: str | None = None
    PrivateKey: str | None = None
    PublicKey: str | None = None


class WGClient(BaseModel):
    ID: str
    Name: str
    Email: str
    IPAllocation: str | None = None
    AllowedIPs: str | None = None
    UseDNS: bool | None = None
    disabled: bool | None = None


class WGClientCreate(BaseModel):
    Name: str
    Email: str
    IPAllocation: str | None = None
    AllowedIPs: str | None = None
    UseDNS: bool = False
    disabled: bool = False
    PublicKey: str | None = None
    PrivateKey: str | None = None
    PresharedKey: str | None = None


class WGClientKeys(BaseModel):
    PublicKey: str | None = None
    PrivateKey: str | None = None
    PresharedKey: str | None = None


class WGServerKeys(BaseModel):
    PublicKey: str | None = None
    PrivateKey: str | None = None


class WGClientCreated(BaseModel):
    ID: str


class WGServerApplyResult(BaseModel):
    result: str
    mode: str
    interface: str
    peer_count: int


class UpdateWGClient(BaseModel):
    Name: str | None = None
    Email: str | None = None
    IPAllocation: str | None = None
    AllowedIPs: str | None = None
    UseDNS: bool | None = None
    disabled: bool | None = None
