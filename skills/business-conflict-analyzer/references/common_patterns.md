# Common Conflict Pattern Library / 常见冲突模式库

> Reference for AI during business impact analysis. Each pattern describes: trigger → business impact → recommended action → scope → fix cost.
> AI 在分析业务冲突时参考。每条模式描述了：触发特征 → 业务影响 → 建议操作 → 影响范围 → 修复代价。

---

## 字段改名 / Field Rename

- **触发特征**：DTO/VO 中字段被删除，同时新增了名称相似的字段
- **Trigger**: A field is deleted from a DTO/VO while a new field with a similar name is added
- **业务影响**：调用方使用旧字段名时编译失败；存量序列化数据中的旧字段丢失
- **Business Impact**: Callers using the old field name fail to compile; serialized data with the old field loses data
- **建议操作**：先同时保留新旧字段（`@JsonProperty` 别名），标记旧字段 `@Deprecated`，下个版本再移除
- **Recommended Action**: Keep both old and new fields simultaneously (via `@JsonProperty` alias), mark the old one `@Deprecated`, remove in a future release
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: API consumers + serialized data
- **修复代价 / Fix Cost**: High (requires two releases)

## 字段类型变更 / Field Type Change

- **触发特征**：DTO/VO 中某个字段的数据类型变化（如 `Long` → `String`）
- **Trigger**: A field's data type changes (e.g., `Long` → `String`)
- **业务影响**：调用方如果用了类型强转或特定格式，会运行时异常
- **Business Impact**: Callers using type casts or specific formatting will get runtime errors
- **建议操作**：如果是为了扩展格式（如 ID 从数字变字符串），应先新增字段，逐步迁移
- **Recommended Action**: If expanding format (e.g., numeric ID → string), add a new field first and migrate gradually
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: API consumers
- **修复代价 / Fix Cost**: Medium (requires data assessment)

## 接口方法参数变化 / API Method Parameter Change

- **触发特征**：Controller/Feign 接口方法参数个数、类型、顺序变化
- **Trigger**: Number, type, or order of parameters on a Controller/Feign method changes
- **业务影响**：HTTP 接口的请求格式变化，已有客户端（前端/第三方）调用失败
- **Business Impact**: HTTP request format changes; existing clients fail to call
- **建议操作**：新增重载方法或新版本接口，旧接口标记 `@Deprecated`
- **Recommended Action**: Add an overloaded method or a new versioned endpoint, mark the old one `@Deprecated`
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Upstream callers (frontend / third-party)
- **修复代价 / Fix Cost**: High (requires API version upgrade)

## 接口返回值变化 / API Return Type Change

- **触发特征**：Controller 方法返回值类型变化（含泛型参数变化）
- **Trigger**: Return type of a Controller method changes (including generic type parameters)
- **业务影响**：前端/下游服务解析响应时可能解析失败
- **Business Impact**: Frontend/downstream services may fail to parse the response
- **建议操作**：如需变更返回值，先新增字段兼容旧格式，再废弃旧字段
- **Recommended Action**: Add new fields compatible with the old format first, then deprecate old fields
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Frontend + downstream services
- **修复代价 / Fix Cost**: Medium (add new fields compatible with old format)

## DDL 删列 / DDL Drop Column

- **触发特征**：`ALTER TABLE … DROP COLUMN …`
- **Trigger**: `ALTER TABLE … DROP COLUMN …`
- **业务影响**：应用代码如果仍引用该列，运行时报错；存量数据丢失
- **Business Impact**: Application code referencing the column crashes; existing data is lost
- **建议操作**：确认代码中无引用后，先发版去掉代码引用，再执行 DDL 删列
- **Recommended Action**: Verify no code references, remove code references in a release first, then execute the DDL
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Database + application code
- **修复代价 / Fix Cost**: High (requires removing references first)

## DDL 改列 / DDL Modify Column

- **触发特征**：`ALTER TABLE … MODIFY COLUMN …` 或 `CHANGE COLUMN …`
- **Trigger**: `ALTER TABLE … MODIFY COLUMN …` or `CHANGE COLUMN …`
- **业务影响**：数据类型变化可能导致已有数据截断或转换失败
- **Business Impact**: Data type changes may cause truncation or conversion failures on existing data
- **建议操作**：确认存量数据兼容新类型，评估数据量级和转换耗时
- **Recommended Action**: Verify existing data is compatible with the new type; assess data volume and conversion time
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Database + existing data
- **修复代价 / Fix Cost**: Medium (requires data compatibility assessment)

## DDL 新增表 / DDL Create Table

- **触发特征**：`CREATE TABLE …`
- **Trigger**: `CREATE TABLE …`
- **业务影响**：无直接破坏性影响，但涉及新功能的底层存储
- **Business Impact**: No direct breaking impact, but involves storage for new features
- **建议操作**：需确认建表规范（字符集、引擎、索引）是否符合标准
- **Recommended Action**: Verify table creation follows standards (charset, engine, indexing)
- **影响等级 / Impact Level**: COMPATIBLE
- **影响范围 / Scope**: Database
- **修复代价 / Fix Cost**: Low (automatic)

## 枚举新增值 / Enum Value Added

- **触发特征**：枚举类新增常量
- **Trigger**: A new enum constant is added
- **业务影响**：涉及到枚举的 switch/if-else 逻辑需要覆盖新值，否则走入默认分支
- **Business Impact**: Switch/if-else logic over the enum may not handle the new value, falling into default branches
- **建议操作**：检查项目内所有对该枚举的 switch/if-else，确保覆盖
- **Recommended Action**: Audit all switch/if-else statements over this enum; ensure coverage
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Business logic layer
- **修复代价 / Fix Cost**: Low (requires switch coverage check)

## 枚举废弃值 / Enum Value Deprecated

- **触发特征**：枚举常量添加 `@Deprecated` 注解
- **Trigger**: An enum constant is annotated with `@Deprecated`
- **业务影响**：存量数据中可能仍有该枚举值，做转换时需兼容
- **Business Impact**: Existing data may still contain this value; conversion must remain compatible
- **建议操作**：确认存量数据已清理完毕再删除
- **Recommended Action**: Confirm existing data has been cleaned up before deletion
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Business logic + existing data
- **修复代价 / Fix Cost**: Medium (requires data cleanup verification)

## 配置项新增 / Config Item Added

- **触发特征**：`application.yml` / `application.properties` 新增配置项
- **Trigger**: New config item in `application.yml` / `application.properties`
- **业务影响**：无直接破坏性影响，新配置项需有默认值
- **Business Impact**: No direct breaking impact; new config items must have defaults
- **建议操作**：确认配置类中有合理的默认值，确保不配置时系统行为正确
- **Recommended Action**: Verify a sensible default exists in the config class
- **影响等级 / Impact Level**: COMPATIBLE
- **影响范围 / Scope**: System configuration
- **修复代价 / Fix Cost**: Low (verify default exists)

## 配置项删除 / Config Item Deleted

- **触发特征**：配置项被删除或注释掉
- **Trigger**: A config item is deleted or commented out
- **业务影响**：如果代码仍有对应 `@Value` 或 `@ConfigurationProperties` 绑定，启动失败
- **Business Impact**: If code still has `@Value` or `@ConfigurationProperties` bindings, startup will fail
- **建议操作**：先确认代码中无引用，再删除配置项
- **Recommended Action**: First verify no code references the config, then delete it
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: System configuration + startup
- **修复代价 / Fix Cost**: High (requires verifying no references)

## 消息体字段变更 / Message Body Field Change

- **触发特征**：MQ 消息体类字段增删改
- **Trigger**: Add/delete/modify fields on an MQ message body class
- **业务影响**：消费者反序列化消息时，字段不匹配导致消费失败或丢失数据
- **Business Impact**: Consumers fail to deserialize or lose data when fields don't match
- **建议操作**：先保证生产者和消费者的消息体版本对齐，再变更
- **Recommended Action**: Align message body versions between producer and consumer before changing
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Message producer + consumers
- **修复代价 / Fix Cost**: High (requires version alignment)

## Feign 接口地址变更 / Feign URL Change

- **触发特征**：`@FeignClient(name=…)` 的 name/path/url 变化
- **Trigger**: `@FeignClient(name=…)` name/path/url changes
- **业务影响**：服务间调用路由变化，可能导致请求发往错误地址
- **Business Impact**: Inter-service routing changes may send requests to incorrect addresses
- **建议操作**：配合注册中心/网关配置同步更新
- **Recommended Action**: Sync updates with the service registry / gateway configuration
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Inter-service calls
- **修复代价 / Fix Cost**: High (requires registry coordination)

## Feign Fallback 变更 / Feign Fallback Change

- **触发特征**：Feign 接口的 fallback 类增删改
- **Trigger**: Add/delete/modify the fallback class of a Feign interface
- **业务影响**：服务熔断降级行为变化，下游不可用时的处理逻辑改变
- **Business Impact**: Circuit breaker / fallback behavior changes; handling of downstream failures changes
- **建议操作**：确认新的降级策略符合业务预期
- **Recommended Action**: Verify the new fallback strategy meets business expectations
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Circuit breaker / fallback
- **修复代价 / Fix Cost**: Medium (verify strategy meets expectations)

## 校验注解变更 / Validation Annotation Change

- **触发特征**：`@NotNull` / `@NotBlank` / `@Size` / `@Pattern` 等注解增删
- **Trigger**: Add/remove annotations like `@NotNull` / `@NotBlank` / `@Size` / `@Pattern`
- **业务影响**：接口入参校验规则放宽或收紧，影响上游调用方的传参行为
- **Business Impact**: Input validation rules loosen or tighten, affecting upstream caller behavior
- **建议操作**：收紧校验时需确认所有调用方已满足新规则
- **Recommended Action**: When tightening, verify all callers already satisfy the new rules
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Upstream callers
- **修复代价 / Fix Cost**: Medium (tightening requires caller verification)

## 缓存注解变更 / Cache Annotation Change

- **触发特征**：`@Cacheable` / `@CacheEvict` / `@CachePut` 增删改
- **Trigger**: Add/delete/modify `@Cacheable` / `@CacheEvict` / `@CachePut`
- **业务影响**：缓存策略变化（如 Key 规则、过期时间），影响数据实时性和一致性
- **Business Impact**: Cache strategy changes (key rules, TTL) affect data freshness and consistency
- **建议操作**：确认缓存变更后不影响数据一致性
- **Recommended Action**: Verify data consistency is not compromised
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Cache + data consistency
- **修复代价 / Fix Cost**: Medium (verify consistency)

## 事务注解变更 / Transaction Annotation Change

- **触发特征**：`@Transactional` 增删或 propagation 属性变化
- **Trigger**: Add/remove `@Transactional` or change propagation attribute
- **业务影响**：事务边界变化，影响数据一致性和回滚行为
- **Business Impact**: Transaction boundary changes affect data consistency and rollback behavior
- **建议操作**：确认事务边界变化不引入脏数据或死锁
- **Recommended Action**: Verify that the change does not introduce dirty reads or deadlocks
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Data consistency
- **修复代价 / Fix Cost**: Medium (verify no dirty data risk)

## 异步/定时任务变更 / Async/Scheduled Task Change

- **触发特征**：`@Async` / `@Scheduled` 增删改
- **Trigger**: Add/delete/modify `@Async` / `@Scheduled`
- **业务影响**：异步行为变化，或定时任务频率/逻辑变化
- **Business Impact**: Async behavior changes, or scheduled task frequency/logic changes
- **建议操作**：确认异步/定时任务的执行频率和逻辑符合业务要求
- **Recommended Action**: Verify the execution frequency and logic match business requirements
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Async task execution
- **修复代价 / Fix Cost**: Low (verify frequency meets expectations)

## Python Django ORM 模型变更 / Django ORM Model Change

- **触发特征**：Django models.py 中的字段增删改，或 migration 文件变更
- **Trigger**: Add/delete/modify fields in Django models.py, or migration file changes
- **业务影响**：数据库表结构变化，影响 ORM 查询和序列化输出
- **Business Impact**: Database schema changes affect ORM queries and serialized output
- **建议操作**：先生成 migration（`makemigrations`），检查自动生成的 migration 文件是否符合预期
- **Recommended Action**: Generate migrations first (`makemigrations`), review the auto-generated file
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: API consumers + database
- **修复代价 / Fix Cost**: Medium (review migration files)

## Python Serializer 字段变更 / Serializer Field Change

- **触发特征**：Django REST Framework serializers.py 或 FastAPI schemas.py 中字段增删改
- **Trigger**: Add/delete/modify fields in DRF serializers.py or FastAPI schemas.py
- **业务影响**：API 响应格式变化，前端/下游解析失败
- **Business Impact**: API response format changes cause frontend/downstream parsing failures
- **建议操作**：新增字段用 `required=False` 兼容旧版本，删除字段前确认无消费者依赖
- **Recommended Action**: Use `required=False` for new fields; verify no consumers depend on deleted fields
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: API consumers
- **修复代价 / Fix Cost**: High (involves API versioning)

## TypeScript Interface 字段变更 / TypeScript Interface Field Change

- **触发特征**：`.ts`/`.tsx` 文件中 interface/type 字段增删改
- **Trigger**: Add/delete/modify fields on interface/type in `.ts`/`.tsx` files
- **业务影响**：前端类型检查失败，编译时报错；运行时可能 undefined
- **Business Impact**: Frontend type check fails at compile time; runtime values may be undefined
- **建议操作**：新增字段用可选类型（`?`），删除字段前扫描项目中所有引用
- **Recommended Action**: Use optional types (`?`) for new fields; scan all references before deleting
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: Frontend + type definition consumers
- **修复代价 / Fix Cost**: Medium (synchronize consumer types)

## Python Flask/FastAPI 路由变更 / Flask/FastAPI Route Change

- **触发特征**：`@app.route()` / `@router.get()` 等路由装饰器的路径或方法变化
- **Trigger**: Path or HTTP method change on `@app.route()` / `@router.get()` decorators
- **业务影响**：API 端点 URL 变化，客户端请求 404
- **Business Impact**: API endpoint URL changes cause client 404 errors
- **建议操作**：保留旧路由重定向到新路由，或通过版本前缀兼容
- **Recommended Action**: Keep old routes with redirects, or use version-prefixed paths
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: All API consumers (frontend, third-party, internal services)
- **修复代价 / Fix Cost**: High (requires consumer migration coordination)

## Go Struct 字段变更 / Go Struct Field Change

- **触发特征**：Go struct 定义中字段增删改，或 tag 标签变化（json, yaml, xml）
- **Trigger**: Add/delete/modify struct fields, or tag changes (json, yaml, xml)
- **业务影响**：JSON 序列化输出变化，下游解析可能失败
- **Business Impact**: JSON serialization output changes; downstream parsers may fail
- **建议操作**：新增字段用 `omitempty` 兼容旧解析器，删除字段前确认所有序列化消费者
- **Recommended Action**: Use `omitempty` for new fields; verify all serialization consumers before deleting
- **影响等级 / Impact Level**: BREAKING
- **影响范围 / Scope**: API consumers + serialized data
- **修复代价 / Fix Cost**: Medium (audit all serialization paths)

## React/Vue 组件 Props 变更 / Component Props Change

- **触发特征**：组件 Props/PropsType/interface 定义变化，或组件接收的参数变化
- **Trigger**: Component Props/PropsType/interface definitions or parameter expectations change
- **业务影响**：父组件传参时报错，或子组件无法正确渲染
- **Business Impact**: Parent components trigger errors when passing props, or child components fail to render
- **建议操作**：新增 props 用可选标记，删除 props 需扫描所有使用该组件的地方
- **Recommended Action**: Mark new props as optional; scan all component usage sites before deleting props
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: Component consumers
- **修复代价 / Fix Cost**: Low (only affects frontend builds)

## Node.js Express 中间件变更 / Express Middleware Change

- **触发特征**：`app.use()` / 中间件函数签名或顺序变化
- **Trigger**: `app.use()` / middleware function signature or order changes
- **业务影响**：请求处理链路变化，可能影响认证/日志/错误处理
- **Business Impact**: Request pipeline changes may affect auth/logging/error handling
- **建议操作**：确保中间件顺序调整后不影响已有请求流程
- **Recommended Action**: Verify the adjusted middleware order does not affect existing request flows
- **影响等级 / Impact Level**: MAJOR
- **影响范围 / Scope**: All API requests
- **修复代价 / Fix Cost**: Medium (full request chain testing required)
