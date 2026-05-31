import os
import pandas as pd
from flask import Blueprint, request, jsonify, session
from sqlalchemy import or_, func
from werkzeug.utils import secure_filename
from datetime import datetime
from .db import db
from .models import DrugCategory, WorkloadSampleMeasurement
from .auth import require_auth


drug_category_bp = Blueprint("drug_category", __name__)


@drug_category_bp.route("/drug-category", methods=["GET"])
@require_auth
def get_drug_categories():
	"""获取药物分类列表（分页）"""
	try:
		page = request.args.get("page", 1, type=int)
		page_size = request.args.get("pageSize", 20, type=int)
		keyword = request.args.get("keyword", "", type=str).strip()

		# 构建查询
		query = DrugCategory.query

		# 搜索条件
		if keyword:
			query = query.filter(
				or_(
					DrugCategory.drug_name.like(f"%{keyword}%"),
					DrugCategory.drug_category.like(f"%{keyword}%")
				)
			)

		# 分页
		pagination = query.order_by(DrugCategory.created_at.desc()).paginate(
			page=page,
			per_page=page_size,
			error_out=False
		)

		return jsonify({
			"categories": [item.to_dict() for item in pagination.items],
			"total": pagination.total,
			"page": page,
			"pageSize": page_size
		})

	except Exception as e:
		return jsonify({"message": f"获取失败: {str(e)}"}), 500


@drug_category_bp.route("/drug-category", methods=["POST"])
@require_auth
def create_drug_category():
	"""新增药物分类"""
	try:
		data = request.get_json() or {}
		drug_name = data.get("drug_name", "").strip()
		drug_category = data.get("drug_category", "").strip()

		if not drug_name:
			return jsonify({"message": "药品名称不能为空"}), 400

		if not drug_category:
			return jsonify({"message": "药品分类不能为空"}), 400

		# 创建新记录
		new_drug = DrugCategory(
			drug_name=drug_name,
			drug_category=drug_category
		)

		db.session.add(new_drug)
		db.session.commit()

		return jsonify({
			"success": True,
			"message": "新增成功",
			"data": new_drug.to_dict()
		})

	except Exception as e:
		db.session.rollback()
		return jsonify({"message": f"新增失败: {str(e)}"}), 500


@drug_category_bp.route("/drug-category/<int:id>", methods=["PUT"])
@require_auth
def update_drug_category(id):
	"""更新药物分类"""
	try:
		drug = DrugCategory.query.get(id)
		if not drug:
			return jsonify({"message": "记录不存在"}), 404

		data = request.get_json() or {}
		drug_name = data.get("drug_name", "").strip()
		drug_category = data.get("drug_category", "").strip()

		if not drug_name:
			return jsonify({"message": "药品名称不能为空"}), 400

		if not drug_category:
			return jsonify({"message": "药品分类不能为空"}), 400

		drug.drug_name = drug_name
		drug.drug_category = drug_category
		drug.updated_at = datetime.utcnow()

		db.session.commit()

		return jsonify({
			"success": True,
			"message": "更新成功",
			"data": drug.to_dict()
		})

	except Exception as e:
		db.session.rollback()
		return jsonify({"message": f"更新失败: {str(e)}"}), 500


@drug_category_bp.route("/drug-category/<int:id>", methods=["DELETE"])
@require_auth
def delete_drug_category(id):
	"""删除药物分类"""
	try:
		drug = DrugCategory.query.get(id)
		if not drug:
			return jsonify({"message": "记录不存在"}), 404

		db.session.delete(drug)
		db.session.commit()

		return jsonify({
			"success": True,
			"message": "删除成功"
		})

	except Exception as e:
		db.session.rollback()
		return jsonify({"message": f"删除失败: {str(e)}"}), 500


@drug_category_bp.route("/drug-category/batch", methods=["DELETE"])
@require_auth
def batch_delete_drug_category():
	"""批量删除药物分类"""
	try:
		data = request.get_json() or {}
		ids = data.get("ids", [])

		if not ids:
			return jsonify({"message": "请选择要删除的数据"}), 400

		# 删除指定ID的记录
		deleted_count = DrugCategory.query.filter(DrugCategory.id.in_(ids)).delete(synchronize_session=False)
		db.session.commit()

		return jsonify({
			"success": True,
			"message": f"成功删除 {deleted_count} 条数据"
		})

	except Exception as e:
		db.session.rollback()
		return jsonify({"message": f"批量删除失败: {str(e)}"}), 500


@drug_category_bp.route("/drug-category/import", methods=["POST"])
@require_auth
def import_drug_category():
	"""导入Excel"""
	try:
		if "file" not in request.files:
			return jsonify({"message": "没有上传文件"}), 400

		file = request.files["file"]
		if file.filename == "":
			return jsonify({"message": "文件名不能为空"}), 400

		# 检查文件扩展名
		if not file.filename.endswith(('.xlsx', '.xls')):
			return jsonify({"message": "只支持Excel文件(.xlsx, .xls)"}), 400

		# 直接从内存中读取Excel文件，不保存到磁盘
		try:
			df = pd.read_excel(file)
		except Exception as e:
			return jsonify({"message": f"Excel文件读取失败: {str(e)}"}), 400

		# 智能识别列名（支持多种列名格式）
		name_column = None
		category_column = None

		# 尝试匹配药品名称列
		name_candidates = ["药品名称", "药物名称", "名称", "已开展的TDM项目", "项目", "药品"]
		for col in df.columns:
			if col in name_candidates:
				name_column = col
				break

		# 尝试匹配药品分类列
		category_candidates = ["药品分类", "药物分类", "分类", "类别"]
		for col in df.columns:
			if col in category_candidates:
				category_column = col
				break

		# 如果没有找到匹配的列，提供详细的错误信息
		if not name_column or not category_column:
			available_columns = ", ".join(df.columns.tolist())
			missing = []
			if not name_column:
				missing.append("药品名称")
			if not category_column:
				missing.append("药品分类")

			return jsonify({
				"message": f"Excel文件缺少必需的列。需要：{', '.join(missing)}。当前文件包含的列：{available_columns}"
			}), 400

		# 导入数据
		import_count = 0
		update_count = 0
		skip_count = 0

		for index, row in df.iterrows():
			try:
				drug_name = str(row[name_column]).strip() if pd.notna(row[name_column]) else ""
				drug_category = str(row[category_column]).strip() if pd.notna(row[category_column]) else ""

				if not drug_name or not drug_category:
					skip_count += 1
					continue

				# 检查是否已存在相同的药品名称
				existing = DrugCategory.query.filter_by(drug_name=drug_name).first()
				if existing:
					# 更新已存在的记录
					existing.drug_category = drug_category
					existing.updated_at = datetime.utcnow()
					update_count += 1
				else:
					# 创建新记录
					new_drug = DrugCategory(
						drug_name=drug_name,
						drug_category=drug_category
					)
					db.session.add(new_drug)
					import_count += 1
			except Exception as e:
				# 记录错误但继续处理其他行
				print(f"处理第 {index + 2} 行时出错: {str(e)}")
				skip_count += 1
				continue

		db.session.commit()

		message = f"导入成功！新增 {import_count} 条，更新 {update_count} 条"
		if skip_count > 0:
			message += f"，跳过 {skip_count} 条"

		return jsonify({
			"success": True,
			"message": message,
			"imported_count": import_count + update_count
		})

	except Exception as e:
		db.session.rollback()
		import traceback
		error_detail = traceback.format_exc()
		print(f"导入失败详细信息:\n{error_detail}")
		return jsonify({"message": f"导入失败: {str(e)}"}), 500


@drug_category_bp.route("/drug-category/statistics", methods=["GET"])
@require_auth
def get_drug_category_statistics():
	"""获取药物分类统计数据（按月份区间）"""
	try:
		year = request.args.get("year", type=int)
		month_start = request.args.get("monthStart", 1, type=int)
		month_end = request.args.get("monthEnd", 12, type=int)

		if not year:
			return jsonify({"code": 400, "message": "年份参数不能为空"}), 400

		if month_start < 1 or month_start > 12 or month_end < 1 or month_end > 12:
			return jsonify({"code": 400, "message": "月份参数必须在1-12之间"}), 400

		if month_start > month_end:
			return jsonify({"code": 400, "message": "起始月份不能大于结束月份"}), 400

		# 判断是否为单月模式
		is_single_month = (month_start == month_end)

		# 获取所有药物分类
		categories = db.session.query(
			DrugCategory.drug_category
		).distinct().all()

		category_list = [cat[0] for cat in categories]

		# 构建药品名称到分类的映射
		drug_name_to_category = {}
		all_drugs = DrugCategory.query.all()
		for drug in all_drugs:
			# 将药品名称按逗号、顿号等分隔符拆分
			names = drug.drug_name.replace('，', ',').replace('、', ',').split(',')
			for name in names:
				name = name.strip()
				if name:
					drug_name_to_category[name] = drug.drug_category

		if is_single_month:
			# 单月模式：统计当前月、上个月、去年同期
			current_month = month_start

			# 计算上个月
			if current_month == 1:
				prev_month = 12
				prev_year = year - 1
			else:
				prev_month = current_month - 1
				prev_year = year

			# 去年同期
			last_year_same_month = current_month
			last_year = year - 1

			# 获取需要的年度数据
			current_samples = WorkloadSampleMeasurement.query.filter_by(year=year).all()
			prev_samples = WorkloadSampleMeasurement.query.filter_by(year=prev_year).all()
			last_year_samples = WorkloadSampleMeasurement.query.filter_by(year=last_year).all()

			# 初始化结果
			result = {}
			for category in category_list:
				result[category] = {
					"current": 0,
					"previous": 0,
					"lastYear": 0
				}

			# 统计当前月数据
			for sample in current_samples:
				project_name = sample.project_name.strip()
				matched_category = None
				for drug_name, category in drug_name_to_category.items():
					if drug_name in project_name or project_name in drug_name:
						matched_category = category
						break
				if matched_category and matched_category in result:
					month_value = getattr(sample, f"month_{current_month}", 0) or 0
					result[matched_category]["current"] += month_value

			# 统计上个月数据
			for sample in prev_samples:
				project_name = sample.project_name.strip()
				matched_category = None
				for drug_name, category in drug_name_to_category.items():
					if drug_name in project_name or project_name in drug_name:
						matched_category = category
						break
				if matched_category and matched_category in result:
					month_value = getattr(sample, f"month_{prev_month}", 0) or 0
					result[matched_category]["previous"] += month_value

			# 统计去年同期数据
			for sample in last_year_samples:
				project_name = sample.project_name.strip()
				matched_category = None
				for drug_name, category in drug_name_to_category.items():
					if drug_name in project_name or project_name in drug_name:
						matched_category = category
						break
				if matched_category and matched_category in result:
					month_value = getattr(sample, f"month_{last_year_same_month}", 0) or 0
					result[matched_category]["lastYear"] += month_value

			# 格式化返回数据（单月模式）
			chart_data = []
			for category, data in result.items():
				chart_data.append({
					"category": category,
					"months": [
						{"month": f"{year}年{current_month}月", "value": data["current"], "type": "current"},
						{"month": f"{prev_year}年{prev_month}月", "value": data["previous"], "type": "previous"},
						{"month": f"{last_year}年{last_year_same_month}月", "value": data["lastYear"], "type": "lastYear"}
					]
				})

			return jsonify({
				"year": year,
				"monthStart": month_start,
				"monthEnd": month_end,
				"isSingleMonth": True,
				"chartData": chart_data
			})

		else:
			# 多月模式：原有逻辑
			# 获取该年度的样品测定量数据
			samples = WorkloadSampleMeasurement.query.filter_by(year=year).all()

			# 按分类统计每个月的监测量
			result = {}
			for category in category_list:
				result[category] = {}
				for month in range(month_start, month_end + 1):
					result[category][f"month_{month}"] = 0

			# 统计数据
			for sample in samples:
				project_name = sample.project_name.strip()

				# 查找该项目名称对应的分类
				matched_category = None
				for drug_name, category in drug_name_to_category.items():
					if drug_name in project_name or project_name in drug_name:
						matched_category = category
						break

				if matched_category and matched_category in result:
					# 统计各月份数据
					for month in range(month_start, month_end + 1):
						month_value = getattr(sample, f"month_{month}", 0) or 0
						result[matched_category][f"month_{month}"] += month_value

			# 格式化返回数据
			chart_data = []
			for category, months_data in result.items():
				category_data = {
					"category": category,
					"months": []
				}
				for month in range(month_start, month_end + 1):
					category_data["months"].append({
						"month": month,
						"value": months_data[f"month_{month}"]
					})
				chart_data.append(category_data)

			return jsonify({
				"year": year,
				"monthStart": month_start,
				"monthEnd": month_end,
				"isSingleMonth": False,
				"chartData": chart_data
			})

	except Exception as e:
		import traceback
		error_detail = traceback.format_exc()
		print(f"获取统计数据失败:\n{error_detail}")
		return jsonify({"message": f"获取统计数据失败: {str(e)}"}), 500
