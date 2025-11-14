"""
Custom Social Account Adapter for Keycloak Role-Based Access Control

This adapter extends G3W-Suite's built-in social account adapter to implement
semi-automatic admin role assignment based on Keycloak roles.

Security Model:
- Keycloak 'admin' role → Django is_staff=True (admin interface access)
- Keycloak 'admin' role → is_superuser=False (requires manual approval)
- Keycloak 'user' role → Standard G3W role assignment via SOCIALACCOUNT_USER_ROLE

This approach provides:
1. Audit trail: All admin access requests are logged
2. Separation of duties: Keycloak admin ≠ automatic G3W superuser
3. Manual approval step: Prevents unauthorized privilege escalation
4. Reduced manual work: Staff access granted automatically

To grant full superuser permissions after is_staff is set:
- Via Django admin: Users > [select user] > set "Superuser status"
- Via database: UPDATE auth_user SET is_superuser=true WHERE username='admin'
"""

import logging
from usersmanage.vendors.allauth.adapter import G3WSocialAccountAdapter

logger = logging.getLogger(__name__)


class KeycloakRoleBasedAdapter(G3WSocialAccountAdapter):
    """
    Custom adapter that extends G3W-Suite's social account adapter
    to implement role-based access control from Keycloak.
    """

    def save_user(self, request, sociallogin, form=None):
        """
        Save user from social login and apply Keycloak role-based permissions.

        This method:
        1. Calls parent to handle standard G3W role assignment (Editor/Viewer)
        2. Extracts roles from Keycloak OIDC token
        3. Grants is_staff=True for users with 'admin' role
        4. Logs all role assignments for audit trail

        Args:
            request: HTTP request object
            sociallogin: SocialLogin instance containing account data
            form: Optional form with additional user data

        Returns:
            User instance with applied permissions
        """
        # Call parent to handle G3W-Suite role assignment (Editor/Viewer levels)
        user = super().save_user(request, sociallogin, form)

        # Extract Keycloak roles from OIDC token
        keycloak_roles = self._get_keycloak_roles(sociallogin)

        # Log all roles for audit trail
        logger.info(
            f"User {user.username} ({user.email}) logged in via Keycloak with roles: {keycloak_roles}"
        )

        # Apply role-based permissions
        if 'admin' in keycloak_roles:
            # Grant admin interface access but NOT full superuser permissions
            user.is_staff = True
            user.save()

            logger.warning(
                f"ADMIN INTERFACE ACCESS GRANTED: User {user.username} has Keycloak 'admin' role. "
                f"is_staff=True has been set. To grant full superuser permissions, "
                f"manually set is_superuser=True via Django admin."
            )

            # Check if user already has superuser status (set manually)
            if user.is_superuser:
                logger.info(
                    f"User {user.username} already has superuser status (manually approved)"
                )
        else:
            # User does not have admin role - log for security monitoring
            logger.debug(
                f"User {user.username} does not have Keycloak 'admin' role. "
                f"Standard G3W-Suite role applied via SOCIALACCOUNT_USER_ROLE setting."
            )

        return user

    def _get_keycloak_roles(self, sociallogin):
        """
        Extract roles from Keycloak OIDC token.

        Keycloak can store roles in different locations depending on configuration:
        - extra_data['roles'] - Direct realm roles (from protocol mapper)
        - extra_data['realm_access']['roles'] - Standard realm access structure
        - extra_data['resource_access']['client-id']['roles'] - Client-specific roles

        This implementation checks all common locations and returns a combined list.

        Args:
            sociallogin: SocialLogin instance containing account data

        Returns:
            List of role names (strings)
        """
        extra_data = sociallogin.account.extra_data
        roles = []

        # Check direct roles claim (from our protocol mapper configuration)
        if 'roles' in extra_data:
            roles_claim = extra_data['roles']
            # Handle both string and list formats
            if isinstance(roles_claim, list):
                roles.extend(roles_claim)
            elif isinstance(roles_claim, str):
                roles.append(roles_claim)

        # Check realm_access structure (standard Keycloak format)
        if 'realm_access' in extra_data:
            realm_roles = extra_data['realm_access'].get('roles', [])
            roles.extend(realm_roles)

        # Check resource_access for client-specific roles
        if 'resource_access' in extra_data:
            # Try to get roles from our specific client
            for client_id, client_data in extra_data['resource_access'].items():
                client_roles = client_data.get('roles', [])
                roles.extend(client_roles)

        # Remove duplicates and return
        return list(set(roles))
