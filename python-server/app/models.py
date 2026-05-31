from __future__ import annotations
from datetime import datetime
from .db import db


class User(db.Model):
    """用户模型"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.LargeBinary(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_safe_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
        }


class AdverseReactionReport(db.Model):
    """药品不良反应报告模型"""
    __tablename__ = "adverse_reaction_reports"

    id = db.Column(db.Integer, primary_key=True)
    report_code = db.Column(db.String(50), nullable=False, index=True, comment="报告表编码")
    report_type_new = db.Column(db.String(20), comment="报告类型-新的")
    severity = db.Column(db.String(20), nullable=False, comment="报告类型-严重程度")
    medical_record_no = db.Column(db.String(50), nullable=False, comment="病历号/门诊号")
    suspect_concurrent = db.Column(db.String(20), nullable=False, comment="怀疑/并用")
    generic_name = db.Column(db.String(200), nullable=False, comment="通用名称")
    manufacturer = db.Column(db.String(200), nullable=False, comment="生产厂家")
    adverse_reaction_name = db.Column(db.String(500), nullable=False, comment="不良反应名称")
    reporter_profession = db.Column(db.String(50), nullable=False, comment="报告人职业")
    reporter_signature = db.Column(db.String(50), nullable=False, comment="报告人签名")
    national_center_receive_time = db.Column(db.DateTime, nullable=False, comment="国家中心接收时间")
    
    import_batch_id = db.Column(db.String(50), comment="导入批次ID")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "report_code": self.report_code,
            "report_type_new": self.report_type_new,
            "severity": self.severity,
            "medical_record_no": self.medical_record_no,
            "suspect_concurrent": self.suspect_concurrent,
            "generic_name": self.generic_name,
            "manufacturer": self.manufacturer,
            "adverse_reaction_name": self.adverse_reaction_name,
            "reporter_profession": self.reporter_profession,
            "reporter_signature": self.reporter_signature,
            "national_center_receive_time": self.national_center_receive_time.isoformat() if self.national_center_receive_time else None,
            "import_batch_id": self.import_batch_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ImportHistory(db.Model):
    """导入历史记录模型"""
    __tablename__ = "import_history"

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50), unique=True, nullable=False, comment="批次ID")
    filename = db.Column(db.String(200), nullable=False, comment="文件名")
    original_filename = db.Column(db.String(200), nullable=False, comment="原始文件名")
    total_records = db.Column(db.Integer, nullable=False, comment="总记录数")
    success_records = db.Column(db.Integer, nullable=False, comment="成功导入记录数")
    failed_records = db.Column(db.Integer, nullable=False, comment="失败记录数")
    status = db.Column(db.String(20), nullable=False, comment="状态: processing/success/failed")
    error_message = db.Column(db.Text, comment="错误信息")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, comment="完成时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "total_records": self.total_records,
            "success_records": self.success_records,
            "failed_records": self.failed_records,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class WorkloadSampleMeasurement(db.Model):
    """样品测定量模型"""
    __tablename__ = "workload_sample_measurement"

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False, comment="项目名称")
    measurement_content = db.Column(db.String(50), nullable=False, comment="测定内容")
    month_1 = db.Column(db.Integer, default=0, comment="1月")
    month_2 = db.Column(db.Integer, default=0, comment="2月")
    month_3 = db.Column(db.Integer, default=0, comment="3月")
    month_4 = db.Column(db.Integer, default=0, comment="4月")
    month_5 = db.Column(db.Integer, default=0, comment="5月")
    month_6 = db.Column(db.Integer, default=0, comment="6月")
    month_7 = db.Column(db.Integer, default=0, comment="7月")
    month_8 = db.Column(db.Integer, default=0, comment="8月")
    month_9 = db.Column(db.Integer, default=0, comment="9月")
    month_10 = db.Column(db.Integer, default=0, comment="10月")
    month_11 = db.Column(db.Integer, default=0, comment="11月")
    month_12 = db.Column(db.Integer, default=0, comment="12月")
    year = db.Column(db.Integer, nullable=False, comment="年份")
    import_batch_id = db.Column(db.String(50), comment="导入批次ID")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_name": self.project_name,
            "measurement_content": self.measurement_content,
            "month_1": self.month_1,
            "month_2": self.month_2,
            "month_3": self.month_3,
            "month_4": self.month_4,
            "month_5": self.month_5,
            "month_6": self.month_6,
            "month_7": self.month_7,
            "month_8": self.month_8,
            "month_9": self.month_9,
            "month_10": self.month_10,
            "month_11": self.month_11,
            "month_12": self.month_12,
            "year": self.year,
            "total": sum([self.month_1, self.month_2, self.month_3, self.month_4, self.month_5, self.month_6,
                          self.month_7, self.month_8, self.month_9, self.month_10, self.month_11, self.month_12]),
            "import_batch_id": self.import_batch_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkloadIncome(db.Model):
    """收入模型"""
    __tablename__ = "workload_income"

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False, comment="项目名称")
    measurement_content = db.Column(db.String(50), nullable=False, comment="测定内容")
    month_1 = db.Column(db.Float, default=0, comment="1月")
    month_2 = db.Column(db.Float, default=0, comment="2月")
    month_3 = db.Column(db.Float, default=0, comment="3月")
    month_4 = db.Column(db.Float, default=0, comment="4月")
    month_5 = db.Column(db.Float, default=0, comment="5月")
    month_6 = db.Column(db.Float, default=0, comment="6月")
    month_7 = db.Column(db.Float, default=0, comment="7月")
    month_8 = db.Column(db.Float, default=0, comment="8月")
    month_9 = db.Column(db.Float, default=0, comment="9月")
    month_10 = db.Column(db.Float, default=0, comment="10月")
    month_11 = db.Column(db.Float, default=0, comment="11月")
    month_12 = db.Column(db.Float, default=0, comment="12月")
    year = db.Column(db.Integer, nullable=False, comment="年份")
    import_batch_id = db.Column(db.String(50), comment="导入批次ID")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_name": self.project_name,
            "measurement_content": self.measurement_content,
            "month_1": self.month_1,
            "month_2": self.month_2,
            "month_3": self.month_3,
            "month_4": self.month_4,
            "month_5": self.month_5,
            "month_6": self.month_6,
            "month_7": self.month_7,
            "month_8": self.month_8,
            "month_9": self.month_9,
            "month_10": self.month_10,
            "month_11": self.month_11,
            "month_12": self.month_12,
            "year": self.year,
            "total": sum([self.month_1, self.month_2, self.month_3, self.month_4, self.month_5, self.month_6,
                          self.month_7, self.month_8, self.month_9, self.month_10, self.month_11, self.month_12]),
            "import_batch_id": self.import_batch_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkloadCriticalValue(db.Model):
    """危急值模型"""
    __tablename__ = "workload_critical_value"

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False, comment="项目名称")
    measurement_content = db.Column(db.String(50), nullable=False, comment="测定内容")
    month_1 = db.Column(db.Integer, default=0, comment="1月")
    month_2 = db.Column(db.Integer, default=0, comment="2月")
    month_3 = db.Column(db.Integer, default=0, comment="3月")
    month_4 = db.Column(db.Integer, default=0, comment="4月")
    month_5 = db.Column(db.Integer, default=0, comment="5月")
    month_6 = db.Column(db.Integer, default=0, comment="6月")
    month_7 = db.Column(db.Integer, default=0, comment="7月")
    month_8 = db.Column(db.Integer, default=0, comment="8月")
    month_9 = db.Column(db.Integer, default=0, comment="9月")
    month_10 = db.Column(db.Integer, default=0, comment="10月")
    month_11 = db.Column(db.Integer, default=0, comment="11月")
    month_12 = db.Column(db.Integer, default=0, comment="12月")
    year = db.Column(db.Integer, nullable=False, comment="年份")
    import_batch_id = db.Column(db.String(50), comment="导入批次ID")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_name": self.project_name,
            "measurement_content": self.measurement_content,
            "month_1": self.month_1,
            "month_2": self.month_2,
            "month_3": self.month_3,
            "month_4": self.month_4,
            "month_5": self.month_5,
            "month_6": self.month_6,
            "month_7": self.month_7,
            "month_8": self.month_8,
            "month_9": self.month_9,
            "month_10": self.month_10,
            "month_11": self.month_11,
            "month_12": self.month_12,
            "year": self.year,
            "total": sum([self.month_1, self.month_2, self.month_3, self.month_4, self.month_5, self.month_6,
                          self.month_7, self.month_8, self.month_9, self.month_10, self.month_11, self.month_12]),
            "import_batch_id": self.import_batch_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DrugCategory(db.Model):
    """药物分类模型"""
    __tablename__ = "drug_category"

    id = db.Column(db.Integer, primary_key=True)
    drug_name = db.Column(db.String(200), nullable=False, comment="药品名称", index=True)
    drug_category = db.Column(db.String(100), nullable=False, comment="药品分类", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "drug_name": self.drug_name,
            "drug_category": self.drug_category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
