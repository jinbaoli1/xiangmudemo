"""科室数据模型"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Department(BaseModel):
    """科室信息"""

    id: str = Field(..., description="科室唯一ID")
    name: str = Field(..., description="科室名称")
    alias: List[str] = Field(default_factory=list, description="科室别名/简称")
    description: str = Field("", description="科室简介")
    common_symptoms: List[str] = Field(default_factory=list, description="常见症状")
    category: str = Field("", description="科室分类：内科/外科/医技等")
    floor: str = Field("", description="所在楼层")
    phone: str = Field("", description="科室电话")
    is_emergency: bool = Field(False, description="是否为急诊科室")

    def all_names(self) -> List[str]:
        """返回科室所有名称（含别名）"""
        return [self.name] + self.alias
