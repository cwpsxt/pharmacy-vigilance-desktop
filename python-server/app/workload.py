"""
工作量数据管理模块
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import pandas as pd
import xlrd
from .db import db
from .models import WorkloadSampleMeasurement, WorkloadIncome, WorkloadCriticalValue
from .auth import require_auth

workload_bp = Blueprint("workload", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xlsx", "xls"}


def allowed_file(filename):
	return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_int(value):
	"""解析整数值，处理空值和公式"""
	if value is None or value == "":
		return 0
	if isinstance(value, (int, float)):
		# 检查是否为 NaN
		if pd.isna(value):
			return 0
		return int(value)
	if isinstance(value, str):
		# 跳过公式
		if value.startswith("="):
			return 0
		try:
			return int(float(value))
		except ValueError:
			return 0
	return 0


def parse_float(value):
	"""解析浮点数值，处理空值和公式"""
	if value is None or value == "":
		return 0.0
	if isinstance(value, (int, float)):
		# 检查是否为 NaN
		if pd.isna(value):
			return 0.0
		return float(value)
	if isinstance(value, str):
		# 跳过公式
		if value.startswith("="):
			return 0.0
		try:
			return float(value)
		except ValueError:
			return 0.0
	return 0.0


@workload_bp.route("/download-template", methods=["GET"])
@require_auth
def download_workload_template():
	"""下载工作量导入模板"""
	try:
		from io import BytesIO
		from flask import send_file
		
		output = BytesIO()
		
		with pd.ExcelWriter(output, engine='openpyxl') as writer:
			# 样品测定量模板
			sample_data = {
				'项目名称': ['示例：血药浓度监测', '示例：抗菌药物监测'],
				'测定内容': ['示例：万古霉素', '示例：头孢类'],
				'1月': [0, 0], '2月': [0, 0], '3月': [0, 0], '4月': [0, 0],
				'5月': [0, 0], '6月': [0, 0], '7月': [0, 0], '8月': [0, 0],
				'9月': [0, 0], '10月': [0, 0], '11月': [0, 0], '12月': [0, 0]
			}
			df_sample = pd.DataFrame(sample_data)
			df_sample.to_excel(writer, sheet_name='样品测定量', index=False)
			
			# 收入模板
			income_data = {
				'项目名称': ['示例：血药浓度监测', '示例：抗菌药物监测'],
				'测定内容': ['示例：万古霉素', '示例：头孢类'],
				'1月': [0.0, 0.0], '2月': [0.0, 0.0], '3月': [0.0, 0.0], '4月': [0.0, 0.0],
				'5月': [0.0, 0.0], '6月': [0.0, 0.0], '7月': [0.0, 0.0], '8月': [0.0, 0.0],
				'9月': [0.0, 0.0], '10月': [0.0, 0.0], '11月': [0.0, 0.0], '12月': [0.0, 0.0]
			}
			df_income = pd.DataFrame(income_data)
			df_income.to_excel(writer, sheet_name='收入', index=False)
			
			# 危急值模板
			critical_data = {
				'项目名称': ['示例：危急值项目1'],
				'测定内容': ['示例：测定内容1'],
				'1月': [0], '2月': [0], '3月': [0], '4月': [0],
				'5月': [0], '6月': [0], '7月': [0], '8月': [0],
				'9月': [0], '10月': [0], '11月': [0], '12月': [0]
			}
			df_critical = pd.DataFrame(critical_data)
			df_critical.to_excel(writer, sheet_name='危急值', index=False)
		
		output.seek(0)
		
		return send_file(
			output,
			as_attachment=True,
			download_name='工作量数据导入模板.xlsx',
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
		)
		
	except Exception as e:
		return jsonify({"success": False, "message": f"下载模板失败: {str(e)}"}), 500


@workload_bp.route("/upload", methods=["POST"])
@require_auth
def upload_workload_file():
	"""上传并导入工作量Excel文件"""
	if "file" not in request.files:
		return jsonify({"success": False, "message": "未选择文件"}), 400

	file = request.files["file"]
	if file.filename == "":
		return jsonify({"success": False, "message": "未选择文件"}), 400

	if not allowed_file(file.filename):
		return jsonify({"success": False, "message": "文件格式不支持，请上传Excel文件"}), 400

	# 获取年份参数（必填）
	year = request.form.get("year")
	if not year:
		return jsonify({"success": False, "message": "请选择导入数据的年份"}), 400

	try:
		year = int(year)
	except ValueError:
		return jsonify({"success": False, "message": "年份格式无效"}), 400

	try:
		# 保存文件
		filename = secure_filename(file.filename)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		saved_filename = f"{timestamp}_{filename}"
		os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
		filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_filename)
		file.save(filepath)

		# 解析Excel文件
		batch_id = str(uuid.uuid4())

		# 使用pandas读取Excel，支持.xls和.xlsx格式
		try:
			# 根据文件扩展名选择合适的方法
			file_ext = os.path.splitext(filepath)[1].lower()
			if file_ext == '.xls':
				# .xls格式使用xlrd直接读取
				workbook = xlrd.open_workbook(filepath)

				# 优先查找与年份匹配的工作表
				sheet = None
				year_str = str(year)
				if year_str in workbook.sheet_names():
					sheet = workbook.sheet_by_name(year_str)
				else:
					# 如果没有找到，使用第一个工作表
					sheet = workbook.sheet_by_index(0)

				# 将xlrd的数据转换为DataFrame
				data = []
				for row_idx in range(sheet.nrows):
					row_data = []
					for col_idx in range(sheet.ncols):
						cell = sheet.cell(row_idx, col_idx)
						row_data.append(cell.value)
					data.append(row_data)
				df = pd.DataFrame(data)
			else:
				# .xlsx格式使用pandas+openpyxl
				# 优先查找与年份匹配的工作表
				try:
					df = pd.read_excel(filepath, sheet_name=str(year), header=None, engine='openpyxl')
				except:
					# 如果没有找到对应年份的工作表，使用第一个
					df = pd.read_excel(filepath, sheet_name=0, header=None, engine='openpyxl')
		except Exception as e:
			return jsonify({"success": False, "message": f"读取Excel文件失败: {str(e)}"}), 400

		# 解析样品测定量（从第3行开始，列B-P）
		# pandas的行索引从0开始，第3行是索引2
		sample_count = 0
		sample_skipped = 0
		for row_idx in range(2, len(df)):  # 从第3行开始（索引2）
			project_name = df.iloc[row_idx, 1]  # B列（索引1）
			measurement_content = df.iloc[row_idx, 2] if pd.notna(df.iloc[row_idx, 2]) else "样品"  # C列（索引2）

			# 跳过空行、总数行、表头行
			if pd.isna(project_name) or project_name == "总数" or project_name == "项目名称":
				continue

			# 跳过测定内容为空或者是"测定内容"（表头）的行
			if pd.isna(measurement_content) or measurement_content == "测定内容":
				continue

			# 只保存测定内容为"样品"的数据，跳过"质控"和"定标"
			if measurement_content != "样品":
				continue

			# 跳过包含公式的行
			if isinstance(project_name, str) and project_name.startswith("="):
				continue

			# 跳过项目名称和测定内容相同的异常行（例如：项目名称="样品", 测定内容="样品"）
			if str(project_name).strip() == str(measurement_content).strip():
				continue

			# 检查数据是否已存在（根据年份、项目名称、测定内容判断）
			existing = WorkloadSampleMeasurement.query.filter_by(
				year=year,
				project_name=str(project_name).strip(),
				measurement_content=str(measurement_content).strip()
			).first()

			if existing:
				sample_skipped += 1
				continue

			# 解析月度数据 (D-O列, 即索引3-14)
			sample = WorkloadSampleMeasurement(
				project_name=str(project_name).strip(),
				measurement_content=str(measurement_content).strip(),
				month_1=parse_int(df.iloc[row_idx, 3]),   # D列
				month_2=parse_int(df.iloc[row_idx, 4]),   # E列
				month_3=parse_int(df.iloc[row_idx, 5]),   # F列
				month_4=parse_int(df.iloc[row_idx, 6]),   # G列
				month_5=parse_int(df.iloc[row_idx, 7]),   # H列
				month_6=parse_int(df.iloc[row_idx, 8]),   # I列
				month_7=parse_int(df.iloc[row_idx, 9]),   # J列
				month_8=parse_int(df.iloc[row_idx, 10]),  # K列
				month_9=parse_int(df.iloc[row_idx, 11]),  # L列
				month_10=parse_int(df.iloc[row_idx, 12]), # M列
				month_11=parse_int(df.iloc[row_idx, 13]), # N列
				month_12=parse_int(df.iloc[row_idx, 14]), # O列
				year=year,
				import_batch_id=batch_id,
			)
			db.session.add(sample)
			sample_count += 1

		# 解析收入数据（从第3行开始，列R-AC）
		income_count = 0
		income_skipped = 0
		for row_idx in range(2, len(df)):  # 从第3行开始（索引2）
			# 收入数据在R列开始(索引17)
			if df.shape[1] <= 17:  # 检查列数
				continue

			project_name = df.iloc[row_idx, 17]  # R列（索引17）
			measurement_content = df.iloc[row_idx, 18] if pd.notna(df.iloc[row_idx, 18]) else "样品"  # S列（索引18）

			# 跳过空行、总数行、表头行
			if pd.isna(project_name) or project_name == "总数" or project_name == "项目名称":
				continue

			# 跳过测定内容为空或者是"测定内容"（表头）的行
			if pd.isna(measurement_content) or measurement_content == "测定内容":
				continue

			# 只保存测定内容为"样品"的数据
			if measurement_content != "样品":
				continue

			# 跳过包含公式的行
			if isinstance(project_name, str) and project_name.startswith("="):
				continue

			# 跳过项目名称和测定内容相同的异常行
			if str(project_name).strip() == str(measurement_content).strip():
				continue

			# 检查数据是否已存在
			existing = WorkloadIncome.query.filter_by(
				year=year,
				project_name=str(project_name).strip(),
				measurement_content=str(measurement_content).strip()
			).first()

			if existing:
				income_skipped += 1
				continue

			# 解析月度收入数据 (T-AE列, 即索引19-30)
			if df.shape[1] > 19:
				income = WorkloadIncome(
					project_name=str(project_name).strip(),
					measurement_content=str(measurement_content).strip(),
					month_1=parse_float(df.iloc[row_idx, 19]) if df.shape[1] > 19 else 0,   # T列
					month_2=parse_float(df.iloc[row_idx, 20]) if df.shape[1] > 20 else 0,   # U列
					month_3=parse_float(df.iloc[row_idx, 21]) if df.shape[1] > 21 else 0,   # V列
					month_4=parse_float(df.iloc[row_idx, 22]) if df.shape[1] > 22 else 0,   # W列
					month_5=parse_float(df.iloc[row_idx, 23]) if df.shape[1] > 23 else 0,   # X列
					month_6=parse_float(df.iloc[row_idx, 24]) if df.shape[1] > 24 else 0,   # Y列
					month_7=parse_float(df.iloc[row_idx, 25]) if df.shape[1] > 25 else 0,   # Z列
					month_8=parse_float(df.iloc[row_idx, 26]) if df.shape[1] > 26 else 0,   # AA列
					month_9=parse_float(df.iloc[row_idx, 27]) if df.shape[1] > 27 else 0,   # AB列
					month_10=parse_float(df.iloc[row_idx, 28]) if df.shape[1] > 28 else 0,  # AC列
					month_11=parse_float(df.iloc[row_idx, 29]) if df.shape[1] > 29 else 0,  # AD列
					month_12=parse_float(df.iloc[row_idx, 30]) if df.shape[1] > 30 else 0,  # AE列
					year=year,
					import_batch_id=batch_id,
				)
				db.session.add(income)
				income_count += 1

		# 解析危急值数据（从第33行开始，列R-AE）
		critical_count = 0
		critical_skipped = 0
		for row_idx in range(32, min(len(df), 100)):  # 从第33行开始（索引32），扩大搜索范围

			if df.shape[1] <= 17:
				continue

			project_name = df.iloc[row_idx, 17]  # R列（索引17）
			measurement_content = df.iloc[row_idx, 18] if pd.notna(df.iloc[row_idx, 18]) else "样品"  # S列（索引18）

			# 跳过空行、总数行、表头行
			if pd.isna(project_name) or project_name == "总数" or project_name == "项目名称":
				continue

			# 跳过测定内容为空或者是"测定内容"（表头）的行
			if pd.isna(measurement_content) or measurement_content == "测定内容":
				continue

			# 跳过包含公式的行
			if isinstance(project_name, str) and project_name.startswith("="):
				continue

			# 跳过非字符串的项目名称
			if not isinstance(project_name, str):
				continue

			# 跳过项目名称和测定内容相同的异常行
			if str(project_name).strip() == str(measurement_content).strip():
				continue

			# 检查数据是否已存在
			existing = WorkloadCriticalValue.query.filter_by(
				year=year,
				project_name=str(project_name).strip(),
				measurement_content=str(measurement_content).strip()
			).first()

			if existing:
				critical_skipped += 1
				continue

			# 解析月度危急值数据 (T-AE列, 即索引19-30)
			if df.shape[1] > 19:
				critical = WorkloadCriticalValue(
					project_name=str(project_name).strip(),
					measurement_content=str(measurement_content).strip(),
					month_1=parse_int(df.iloc[row_idx, 19]) if df.shape[1] > 19 else 0,   # T列
					month_2=parse_int(df.iloc[row_idx, 20]) if df.shape[1] > 20 else 0,   # U列
					month_3=parse_int(df.iloc[row_idx, 21]) if df.shape[1] > 21 else 0,   # V列
					month_4=parse_int(df.iloc[row_idx, 22]) if df.shape[1] > 22 else 0,   # W列
					month_5=parse_int(df.iloc[row_idx, 23]) if df.shape[1] > 23 else 0,   # X列
					month_6=parse_int(df.iloc[row_idx, 24]) if df.shape[1] > 24 else 0,   # Y列
					month_7=parse_int(df.iloc[row_idx, 25]) if df.shape[1] > 25 else 0,   # Z列
					month_8=parse_int(df.iloc[row_idx, 26]) if df.shape[1] > 26 else 0,   # AA列
					month_9=parse_int(df.iloc[row_idx, 27]) if df.shape[1] > 27 else 0,   # AB列
					month_10=parse_int(df.iloc[row_idx, 28]) if df.shape[1] > 28 else 0,  # AC列
					month_11=parse_int(df.iloc[row_idx, 29]) if df.shape[1] > 29 else 0,  # AD列
					month_12=parse_int(df.iloc[row_idx, 30]) if df.shape[1] > 30 else 0,  # AE列
					year=year,
					import_batch_id=batch_id,
				)
				db.session.add(critical)
				critical_count += 1

		db.session.commit()

		# 构建导入结果消息
		message_parts = []
		if sample_count > 0:
			message_parts.append(f"样品测定量: {sample_count}条")
		if sample_skipped > 0:
			message_parts.append(f"(跳过{sample_skipped}条重复)")

		if income_count > 0:
			message_parts.append(f"收入: {income_count}条")
		if income_skipped > 0:
			message_parts.append(f"(跳过{income_skipped}条重复)")

		if critical_count > 0:
			message_parts.append(f"危急值: {critical_count}条")
		if critical_skipped > 0:
			message_parts.append(f"(跳过{critical_skipped}条重复)")

		message = f"导入成功！{year}年数据：" + "，".join(message_parts)

		return jsonify({
			"success": True,
			"message": message,
			"data": {
				"batch_id": batch_id,
				"year": year,
				"sample_count": sample_count,
				"sample_skipped": sample_skipped,
				"income_count": income_count,
				"income_skipped": income_skipped,
				"critical_count": critical_count,
				"critical_skipped": critical_skipped,
			}
		})

	except Exception as e:
		db.session.rollback()
		return jsonify({"success": False, "message": f"导入失败: {str(e)}"}), 500


@workload_bp.route("/sample-measurement", methods=["GET"])
@require_auth
def get_sample_measurements():
	"""获取样品测定量数据"""
	year = request.args.get("year", type=int)
	page = request.args.get("page", 1, type=int)
	page_size = request.args.get("page_size", 20, type=int)

	query = WorkloadSampleMeasurement.query
	if year:
		query = query.filter_by(year=year)

	query = query.order_by(WorkloadSampleMeasurement.created_at.desc())

	pagination = query.paginate(page=page, per_page=page_size, error_out=False)

	return jsonify({
		"success": True,
		"data": {
			"items": [item.to_dict() for item in pagination.items],
			"total": pagination.total,
			"page": page,
			"page_size": page_size,
		}
	})


@workload_bp.route("/income", methods=["GET"])
@require_auth
def get_income():
	"""获取收入数据"""
	year = request.args.get("year", type=int)
	page = request.args.get("page", 1, type=int)
	page_size = request.args.get("page_size", 20, type=int)

	query = WorkloadIncome.query
	if year:
		query = query.filter_by(year=year)

	query = query.order_by(WorkloadIncome.created_at.desc())

	pagination = query.paginate(page=page, per_page=page_size, error_out=False)

	return jsonify({
		"success": True,
		"data": {
			"items": [item.to_dict() for item in pagination.items],
			"total": pagination.total,
			"page": page,
			"page_size": page_size,
		}
	})


@workload_bp.route("/critical-value", methods=["GET"])
@require_auth
def get_critical_values():
	"""获取危急值数据"""
	year = request.args.get("year", type=int)
	page = request.args.get("page", 1, type=int)
	page_size = request.args.get("page_size", 20, type=int)

	query = WorkloadCriticalValue.query
	if year:
		query = query.filter_by(year=year)

	query = query.order_by(WorkloadCriticalValue.created_at.desc())

	pagination = query.paginate(page=page, per_page=page_size, error_out=False)

	return jsonify({
		"success": True,
		"data": {
			"items": [item.to_dict() for item in pagination.items],
			"total": pagination.total,
			"page": page,
			"page_size": page_size,
		}
	})


@workload_bp.route("/data", methods=["GET"])
@require_auth
def get_all_workload_data():
	"""获取所有工作量数据(用于前端加载)"""
	try:
		year = request.args.get("year", type=int)

		# 获取样品测定量数据
		sample_query = WorkloadSampleMeasurement.query
		if year:
			sample_query = sample_query.filter_by(year=year)
		sample_data = [item.to_dict() for item in sample_query.all()]

		# 获取收入数据
		income_query = WorkloadIncome.query
		if year:
			income_query = income_query.filter_by(year=year)
		income_data = [item.to_dict() for item in income_query.all()]

		# 获取危急值数据
		critical_query = WorkloadCriticalValue.query
		if year:
			critical_query = critical_query.filter_by(year=year)
		critical_data = [item.to_dict() for item in critical_query.all()]

		return jsonify({
			"success": True,
			"data": {
				"sample": sample_data,
				"income": income_data,
				"critical": critical_data,
			}
		})
	except Exception as e:
		return jsonify({"success": False, "message": f"获取数据失败: {str(e)}"}), 500


@workload_bp.route("/data/<data_type>", methods=["DELETE"])
@require_auth
def delete_all_workload_data(data_type):
	"""删除指定类型的所有工作量数据"""
	try:
		if data_type == "sample":
			WorkloadSampleMeasurement.query.delete()
		elif data_type == "income":
			WorkloadIncome.query.delete()
		elif data_type == "critical":
			WorkloadCriticalValue.query.delete()
		else:
			return jsonify({"success": False, "message": "无效的数据类型"}), 400

		db.session.commit()
		return jsonify({"success": True, "message": "删除成功"})
	except Exception as e:
		db.session.rollback()
		return jsonify({"success": False, "message": f"删除失败: {str(e)}"}), 500


@workload_bp.route("/delete/<data_type>/<int:id>", methods=["DELETE"])
@require_auth
def delete_workload_data(data_type, id):
	"""删除单条工作量数据"""
	try:
		if data_type == "sample":
			item = WorkloadSampleMeasurement.query.get_or_404(id)
		elif data_type == "income":
			item = WorkloadIncome.query.get_or_404(id)
		elif data_type == "critical":
			item = WorkloadCriticalValue.query.get_or_404(id)
		else:
			return jsonify({"success": False, "message": "无效的数据类型"}), 400

		db.session.delete(item)
		db.session.commit()

		return jsonify({"success": True, "message": "删除成功"})
	except Exception as e:
		db.session.rollback()
		return jsonify({"success": False, "message": f"删除失败: {str(e)}"}), 500
