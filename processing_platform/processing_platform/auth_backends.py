from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class FeideBackend(OIDCAuthenticationBackend):
    ALLOWED_ORGS = {"nmbu.no"}

    ROLE_MAP = {
        "fc:org:nmbu.no:role=staff":  ("staff",  "editor"),
        "fc:org:nmbu.no:role=student":("student",),
    }

    def verify_claims(self, claims):
        base_ok = super().verify_claims(claims)
        org_ok  = claims.get("schacHomeOrganization") in self.ALLOWED_ORGS
        return base_ok and org_ok

    def create_user(self, claims):
        user = super().create_user(claims)
        user.email = claims.get("email")
        user.first_name, *_last = (claims.get("name") or "").split(" ", 1)
        user.last_name = _last[0] if _last else ""
        return user

    def update_user(self, user, claims):
        user.groups.clear()

        for feide_gid, django_groups in self.ROLE_MAP.items():
            if feide_gid in claims.get("groups", []):
                for name in django_groups:
                    group, _ = Group.objects.get_or_create(name=name)
                    user.groups.add(group)

        user.is_staff = user.groups.filter(name="staff").exists()
        user.save()
        return user
