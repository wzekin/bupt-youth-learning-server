# 柏油青年大学习API

## User 用户API

### 获取当前用户信息
* url: /user/me/
* method: GET
* auth: True
* input: null
* output:
``` json
HTTP 200 OK
Allow: GET, PUT, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "id": 2018211236,
    "permissions": [
        {
            "id": 2,
            "user_id": 2018211236,
            "permission_type": 6,
            "permission_id": 2,
            "permission_name": "xxx"
        }
    ],
    "last_login": "2020-08-23T11:21:29.768294Z",
    "name": "王泽坤",
    "continue_study": 0,
    "modified": "2020-08-23T11:21:09.522935Z",
    "created": "2020-08-23T11:21:09.522959Z",
    "college": null,
    "league_branch": null
}
```

### 修改当前用户信息
* url: /user/me/
* method: PUT
* auth: True
* input:
``` json
{
    "college": 2,
    "league_branch": null
}
```

* output
``` json
HTTP 200 OK
Allow: GET, PUT, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "id": 2018211236,
    "permissions": [
        {
            "id": 2,
            "user_id": 2018211236,
            "permission_type": 6,
            "permission_id": 2,
            "permission_name": "xxx"
        }
    ],
    "last_login": "2020-08-23T11:21:29.768294Z",
    "name": "王泽坤",
    "continue_study": 0,
    "modified": "2020-08-23T12:01:13.175131Z",
    "created": "2020-08-23T11:21:09.522959Z",
    "college": 2,
    "league_branch": null
}
```

## College 学院API

### 获取所有学院信息
* url: /college
* method: GET
* auth: 所有用户
* input: null
* output:
``` json
[
    {
        "id": 1,
        "name": "xxx",
        "created": "2020-08-23T11:29:44.322758Z"
    }
]
```


### 新增学院信息
* url: /college
* method: POST
* auth: 校级管理员(is_superuser = True)
* input:
``` json
{
    "name": "xxx"
}
```
* output:
``` json
HTTP 201 Created
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "id": 1,
    "name": "xxx",
    "created": "2020-08-23T11:29:44.322758Z"
}
```

### 删除学院信息
* url: /college/:id/
* method: DELETE
* auth: 校级管理员(is_superuser = True)
* input: null
* output:
``` json
HTTP 204 No Content
Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

```

## LeagueBranch 团支部API

### 获取所有学院信息
* url: /league_branch/
* method: GET
* auth: 所有用户
* input: null
* output: 
``` json
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

[
    {
        "id": 2,
        "name": "xxx",
        "created": "2020-08-23T11:37:58.352806Z",
        "college": 2
    }
]
```

### 新增学院信息
* url: /league_branch/
* method: POST
* auth: 校级管理员(is_superuser = True) 以及所对应学院的管理员
* input: 
``` json
{
    "name": "xxx",
    "college": 2
}
```
* output:
``` json
HTTP 201 Created
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "id": 2,
    "name": "xxx",
    "created": "2020-08-23T11:37:58.352806Z",
    "college": 2
}
```

### 删除学院信息
* url: /league_branch/:id/
* method: DELETE
* auth: 校级管理员(is_superuser = True) 以及所对应学院的管理员
* input: null
* output: 
``` json
HTTP 204 No Content
Allow: DELETE, OPTIONS
Content-Type: application/json
Vary: Accept

```

## Permission 权限API
### 新增学院信息
* url: /league_branch/
* method: POST
* auth: 校级管理员(is_superuser = True) 以及所对应学院的管理员
* input:
``` json
{
    "user_id": 2018211236,
    "permission_type": 6,
    "permission_id": 2,
}
```
* output:
``` json
{
    "id": 2,
    "user_id": 2018211236   ,
    "permission_type": 6,
    "permission_id": 2,
    "permission_name": "xxx"
}

```

### 删除学院信息
* url: /league_branch/:id/
* method: DELETE
* auth: 校级管理员(is_superuser = True) 以及所对应学院的管理员
* input: null
* output: 同上

## StudyPeriod