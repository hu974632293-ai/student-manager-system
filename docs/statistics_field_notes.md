# 统计模块字段与代码讲解

## 一、数据库表字段中文含义

### classes 班级表

| 字段 | 中文含义 | 统计模块中的作用 |
| --- | --- | --- |
| id | 班级主键ID | students.class_id 关联到这里 |
| class_id | 班级编号 | 接口对外展示的班级标识，如 AI0409 |
| start_date | 开课时间 | 班级基础信息 |
| head_teacher | 班主任 | 班级基础信息 |
| description | 班级描述 | 展示班级方向或说明 |
| is_deleted | 是否删除 | 统计时过滤已删除班级 |

### teachers 教师表

| 字段 | 中文含义 | 统计模块中的作用 |
| --- | --- | --- |
| id | 教师主键ID | students.consultant_id 关联到这里 |
| teacher_number | 工号 | 教师业务编号 |
| name | 姓名 | 教师姓名 |
| gender | 性别 | 教师基础信息 |
| phone | 电话 | 联系方式 |
| email | 邮箱 | 联系方式 |
| subject | 教授科目 | 教师授课方向 |
| is_active | 是否在职 | 教师状态 |
| is_deleted | 是否删除 | 教师模块软删除标记 |

### students 学生表

| 字段 | 中文含义 | 统计模块中的作用 |
| --- | --- | --- |
| id | 学生主键ID | 数据库内部主键 |
| student_id | 学生编号 | 关联成绩表和就业表的业务编号 |
| class_id | 学生班级 | 关联 classes.id |
| name | 学生姓名 | 统计结果展示 |
| native_place | 籍贯 | 学生基础资料 |
| graduate_school | 毕业院校 | 学生基础资料 |
| major | 专业 | 学生基础资料 |
| enrollment_date | 入学日期 | 学生基础资料 |
| graduation_date | 毕业日期 | 学生基础资料 |
| education | 学历 | 学生基础资料 |
| consultant_id | 顾问编号 | 关联 teachers.id |
| age | 年龄 | 年龄统计的核心字段 |
| gender | 性别 | 班级男女比例统计的核心字段 |
| is_deleted | 是否删除 | 统计时过滤已删除学生 |

### student_scores 成绩表

| 字段 | 中文含义 | 统计模块中的作用 |
| --- | --- | --- |
| id | 成绩主键ID | 数据库内部主键 |
| student_id | 学生编号 | 关联 students.student_id |
| exam_round | 考核序次 | 区分第几次考试 |
| score | 分数 | 达标、不及格、平均分统计核心字段 |
| remark | 备注 | 成绩说明 |

### student_jobs 就业表

| 字段 | 中文含义 | 统计模块中的作用 |
| --- | --- | --- |
| id | 就业主键ID | 数据库内部主键 |
| student_id | 学生编号 | 关联 students.student_id |
| name | 学生姓名冗余 | 就业统计展示 |
| class_name | 班级名称冗余 | 就业时长按班级过滤和分组 |
| job_open_date | 就业开放时间 | 计算就业耗时的起点 |
| offer_date | Offer 下发时间 | 计算就业耗时的终点 |
| company_name | 公司名称 | 薪资 TopN 展示 |
| salary | 薪资 | 薪资排名核心字段 |
| position | 职位 | 就业岗位信息 |
| is_deleted | 是否删除 | 统计时过滤已删除就业记录 |

### class_teacher_link 班级教师关联表

| 字段 | 中文含义 | 统计模块中的作用 |
| --- | --- | --- |
| class_id | 班级ID | 关联 classes.id |
| teacher_id | 教师ID | 关联 teachers.id |

## 二、统计模块数据走向

整体设计是三层：`API/API_statistics.py` 接收请求，`Dao/Dao_statistics.py` 查询数据库，`Scheme/Schemas_statistics.py` 定义返回结构。

1. 用户访问 `/statistics/...` 接口。
2. FastAPI 根据 `Query` 配置校验参数，例如分数必须在 0 到 100 之间。
3. `Depends(get_db)` 创建数据库会话。
4. API 函数调用 `statistics_dao` 对应方法。
5. DAO 使用 SQLAlchemy 构造查询，完成过滤、连表、分组、聚合和排序。
6. 查询结果通过 Pydantic 响应模型转成 JSON 返回。

## 三、重点接口答辩讲法

`/statistics/students/over-30`：从 students 表查询年龄大于阈值且未删除的学生，默认阈值是 30。

`/statistics/classes/gender-count`：从 classes 表出发外连接 students 表，按班级编号分组，统计总人数、男生人数、女生人数。使用外连接是为了保留没有学生的班级。

`/statistics/scores/all-above-80`：先在 student_scores 表按学生分组，使用最低分判断这个学生是否所有成绩都达标，再回查并返回每轮成绩明细。

`/statistics/scores/failed-more-than-twice`：先统计每个学生低于不及格线的次数，筛出超过阈值的学生，再返回这些学生的不及格成绩明细。

`/statistics/scores/class-average`：连接成绩、学生、班级三张表，按考试轮次和班级编号分组，用 `avg(score)` 得到平均分。

`/statistics/employment/top5-salary`：从就业表读取薪资，连接学生和班级过滤无效数据，按薪资倒序取前 N 名。

`/statistics/employment/student-duration`：用 `datediff(offer_date, job_open_date)` 计算每个学生从就业开放到 Offer 下发经过的天数。

`/statistics/employment/class-average-duration`：在单个学生就业耗时的基础上，按班级分组求平均就业时长。
