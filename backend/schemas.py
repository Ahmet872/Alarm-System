from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Union, List
from datetime import datetime
from models import AssetClass, AlarmType

# Alarm modelleri
class AlarmBase(BaseModel):
    asset_class: AssetClass
    asset_symbol: str = Field(..., min_length=1, max_length=15)
    alarm_type: AlarmType
    params: Dict[str, Union[float, int]]  # Sadece numeric değerler
    email: EmailStr

    @field_validator('params')
    def validate_params(cls, v: Dict[str, Any], info: Any) -> Dict[str, Any]:
        alarm_type = info.data.get('alarm_type')
        try:
            if alarm_type == AlarmType.PRICE:
                if 'target_price' not in v:
                    raise ValueError('Price alarm requires target_price parameter')
                target_price = float(v['target_price'])
                if target_price <= 0:
                    raise ValueError('target_price must be positive')
                v['target_price'] = target_price

            elif alarm_type == AlarmType.RSI:
                required = {'period', 'threshold'}
                if not all(k in v for k in required):
                    raise ValueError(f'RSI alarm requires parameters: {required}')
                period = int(v['period'])
                threshold = float(v['threshold'])
                if period <= 0:
                    raise ValueError('period must be positive')
                if not 0 <= threshold <= 100:
                    raise ValueError('threshold must be between 0 and 100')
                v['period'] = period
                v['threshold'] = threshold

            elif alarm_type == AlarmType.BOLLINGER:
                required = {'period', 'std_dev'}
                if not all(k in v for k in required):
                    raise ValueError(f'Bollinger alarm requires parameters: {required}')
                period = int(v['period'])
                std_dev = float(v['std_dev'])
                if period <= 0:
                    raise ValueError('period must be positive')
                if std_dev <= 0:
                    raise ValueError('std_dev must be positive')
                v['period'] = period
                v['std_dev'] = std_dev

            return v
        except (TypeError, ValueError) as e:
            raise ValueError(f'Parameter validation failed: {str(e)}')


class AlarmCreate(AlarmBase):
    pass


class Alarm(AlarmBase):
    id: int
    created_at: datetime
    status: str

    class Config:
        from_attributes = True  # V2 syntax for orm_mode


class AlarmInDB(Alarm):
    pass


# Yeni eklenen: AssetsResponse modeli
class AssetModel(BaseModel):
    symbol: str
    name: str
    price: float

class AssetsResponse(BaseModel):
    asset_class: AssetClass
    assets: List[AssetModel]
