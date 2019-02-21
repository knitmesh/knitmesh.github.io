---
layout:     post
title:      "Role delegation in keystone: Trusts"
subtitle:   "This article introduces Keystone's trusts mechanism and gives a quick example showing how to use a trust to access a swift container on behalf of another user."
date:       2017-03-10 12:00:00
author:     "Jingh"
header-img: "img/bg-footer.jpg"
catalog: true
tags: [OpenStack, OAuth, Keystone]

---

### What are trusts ?
As OpenStack's identity service, Keystone deals with the problems of  authentication ( **who am I ?** ) and authorization ( **what can I do ?** ). The trusts API adds delegation functionalities: by defining a trust relationship between two users, one user (the " **trustor** ") can delegate a limited set of her own rights to  another one (the " **trustee** ") for a limited time. The trust can eventually allow the trustee to impersonate the trustor.


Of course, a lot of safeties are implemented: for example, if a trustor loses a given role, any trusts she issued with that role, and the related tokens, are automatically revoked.


The applications are plentiful:
* Have a service launch an instance on behalf of a user without the user having to authenticate (pretty useful for autoscaling at 3AM). Currently, this is done in Heat by storing the user's credentials somewhere. This is obviously bad from a security point of view.
* Delegate restricted nova API access to (implicitly) untrusted in-instance processes.
* Provide access to accounts and containers on swift without using ACLs.

[The trusts API is described here][1]

### How does it work ?
Since at the time of this writing, there is no support for the trusts API through the keystone client, let's experiment with the API through cURL calls.


Here's the setting:

* Two tenants: TestTenant1 and TestTenant2 
* User1, associated to TestTenant1, has two roles on this tenant: "Member" and "MyFancyRole". The first one allows User1 to upload data on swift. 
* User2, associated to TestTenant2, with no specific role. 
* User1 will allow User2 to upload data on swift on her behalf.

First, User1 needs to get a token from keystone. Trusts are part of the v3 API, so we will request a token the v3 way:

```python
curl -i -d '{ "auth": { "identity": { "methods": [ "password" ], 
"password": { "user": { "id": "User1", "password": "User1" } } } } }' -H 
"Content-type: application/json" http://keystone.url:35357/v3/auth/tokens| awk '{if ($1 =="X-Subject-Token:") {print $2}}' | col -b
```
Then, User1 creates a trust to allow User2 to impersonate her on TestTenant1, with the "Member" role. Since users can be linked to several tenants, it is important to specify the scope of the trust. User1 will also specify the expiry date of the trust. Here is the cURL call:

```python
curl -H "X-Auth-Token: USER1TOKEN" -d '{ "trust": { "expires_at": "2024-02-27T18:30:59.999999Z", "impersonation": true, "project_id": "TestTenant1", "roles": [ { "name": "Member" } ], "trustee_user_id": "'$USER2'", "trustor_user_id": "'$USER1'" }}' -H "Content-type: application/json" http://$URL:35357/v3/OS-TRUST/trusts
```

This is what we get back from keystone:

```python
{
 "trust": {
 "expires_at": "2024-02-27T18:30:59.999999Z", 
 "id": "2d2bef92c56142238142a50b451acc9c", 
 "impersonation": false, 
 "links": {
   "self": "http://keystone.url:5000/v3/trusts/2d2bef92c56142238142a50b451acc9c"
 }, 
 "project_id": "4cbc8f13acb246a29d2241bc4a25984f", 
 "roles": [
   {
     "id": "833ed2da437a49d198a90b224bd03cc3", 
     "links": {
       "self": "http://keystone.url:5000/v3/roles/833ed2da437a49d198a90b224bd03cc3"
      }, 
    "name": "Member"
   }
 ], 
 "roles_links": {
   "next": null, 
   "previous": null, 
   "self": "http://keystone.url:5000/trusts/2d2bef92c56142238142a50b451acc9c/roles"
 }, 
 "trustee_user_id": "d8f9f56949e745bf97c4157d67b3fb24", 
 "trustor_user_id": "9a9f2259dae24a3695c91aa76104285b"
 }
}
```
This is it for User1. Now if User2 wants to do something on behalf of User1, all she needs is her own token (see above) and the trust id to request a trust token. This is done this way:

```python
curl -i -d '{ "auth" : { "identity" : { "methods" : [ "token" ], "token" : { "id" : "USER2_TOKEN" } }, "scope" : { "OS-TRUST:trust" : { "id" : "2d2bef92c56142238142a50b451acc9c" } } } }' -H "Content-type: application/json" http://keystone.url:35357/v3/auth/tokens| awk '{if ($1 =="X-Subject-Token:") {print $2}}'
```
The trust token obtained this way can now be used to authenticate against any service. For example, with swift:

```python
swift --os-auth-token TRUSTTOKEN --os-storage-url http://swift.url:8080/v1/AUTH_TENANT1ID -V 2 list container
```
Here's what will appear in swift's logs:

```python
Here's what will appear in swift's logs:

proxy-server Storing TRUSTTOKEN token in memcache
proxy-server STDOUT: WARNING:root:parameter timeout has been deprecated, use time (txn: txedd37c6afd9246459d1cf-0051e41204)
proxy-server Using identity: {'roles': [u'Member'], 'user': u'User1', 'tenant': (u'58aa10296ed94ea696a83817e43f6d40', u'TestTenant1')} (txn: txedd37c6afd9246459d1cf-0051e41204)
```
Since impersonation was set to true, the transaction appears to originate from User1 and Tenant1. The only way to differentiate this from a genuine connection from User1 is by checking the roles of the user: the real User1 should have also the "MyFancyRole" role listed here.

### What is next ?

The trusts mechanism is brand new. It still needs to be implemented client-side, and then it can be used by other services, namely heat, which has been in dire need of delegation support for a while.

In parallel, support for oAuth-style (v1.0a) delegation is being added to keystone. The main difference with trusts is that the trustee (called " **Consumer** " in oAuth terminology) is the one issueing an access request (along with specific roles to delegate) that needs to be authorized by the trustor (the " **Resource Owner** "). A lot of information needs to be transfered between the Consumer and the Resource Owner out of band (ie outside of keystone's scope), which is usually taken care of by the redirection mechanisms in classic oAuth schemes. This could be implemented at the Horizon level.

Lots of improvements in terms of authorization and delegation are coming to Openstack, so stay tuned !

**Bibliography**
* A comparison of oAuth and trusts by the implementor of trusts: [http://adam.younglogic.com/2013/03/trusts-and-oauth/][2]
* Trusts specifications: [https://wiki.openstack.org/wiki/Keystone/Trusts][3]
* Trusts implementation: [https://review.openstack.org/#/c/20289/][4]
* oAuth implementation (review in progress): [https://review.openstack.org/#/c/29130/][5]

**Script**
The cURL commands in this article come from some test code I wrote to play around with trusts and the ongoing oAuth patches. The code is available here:   [https://github.com/mhuin/keystone_trust][6]


[1]: https://github.com/openstack/identity-api/blob/master/openstack-identity-api/v3/src/markdown/identity-api-v3-os-trust-ext.md
[2]: http://adam.younglogic.com/2013/03/trusts-and-oauth/
[3]: https://wiki.openstack.org/wiki/Keystone/Trusts
[4]: https://review.openstack.org/#/c/20289/
[5]: https://review.openstack.org/#/c/29130/
[6]: https://github.com/mhuin/keystone_trust