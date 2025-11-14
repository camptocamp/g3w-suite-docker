# G3W-SUITE-DOCKER

[![Build G3W-SUITE image](https://github.com/g3w-suite/g3w-suite-docker/actions/workflows/build_and_push_main_image.yml/badge.svg)](https://github.com/g3w-suite/g3w-suite-docker/actions/workflows/build_and_push_main_image.yml)
[![Build G3W-SUITE LTR dependencies](https://github.com/g3w-suite/g3w-suite-docker/actions/workflows/build_and_push_deps_ltr.yml/badge.svg)](https://github.com/g3w-suite/g3w-suite-docker/actions/workflows/build_and_push_deps_ltr.yml)

Run a self hosted web-gis application with Docker Compose

<details>

<summary><h2> ⬆️ How to upgrade from v3.7 to v3.8 </h2></summary>

Since **v3.8** PostgreSQL/PostGIS changed from **v11/2.5** to **v16/3.4**, to upgrade follow below steps:

```sh
# NB:
# • (ENV = dev)      → docker-compose-dev.yml
# • (ENV = prod)     → docker-compose.yml
# • (ENV = consumer) → docker-compose-consumer.yml

### BACKUP (v3.7.x) ###

docker compose up -f docker-compose-dev.yml up -d

git fetch
git checkout v3.8.x

make db-backup ID=11 ENV=prod

### RESTORE (v3.8.x) ###

make db-restore ID=11 ENV=prod

### OPTIONAL (delete old DB) ###

docker compose exec g3w-suite bash -c 'rm -r /shared-volume/11'
docker compose exec g3w-suite bash -c 'rm -r /shared-volume/backup/11'
```
  
</details>

---

![Docker structure](docs/img/docker.png)


## 🌍 Deploying your webgis app

Install [docker compose](https://docs.docker.com/compose/install/).

Clone this repository:

```
git clone https://github.com/g3w-suite/g3w-suite-docker/
cd g3w-suite-docker
```

Create a `.env` file starting from [`.env.example`](./.env.example) and tailor it to your needs:

```diff
# CHANGE ME: PostGIS DB password

- G3WSUITE_POSTGRES_PASS='89#kL8y3D'
+ G3WSUITE_POSTGRES_PASS=<your__password>
```

Start containers:

```sh
docker-compose up -d
```

or, if you intend to use [huey](https://github.com/coleifer/huey) (batch processing)

```sh
docker-compose -f docker-compose-consumer.yml up -d
```

**NB:** at the very first start, have a lot of patience 😴 → the system must finalize the installation. \*

After some time the suite will be available at:

- http://localhost:8080 (user: `admin`, pass: `admin`)

![Login Page](docs/img/login_page.png)

\* in case of faulty container (eg. the first time you didn't wait long enough before trying to access):

```sh
# 🚨 deletes all data
make db-reset ENV=prod

# or
# make db-reset ENV=consumer
```

## 🔐 Keycloak SSO Authentication

This deployment includes Keycloak for Single Sign-On (SSO) authentication using OpenID Connect (OIDC) via **django-allauth**, following the [official G3W-Suite approach](https://g3w-suite.readthedocs.io/en/latest/social_authentication.html).

### Why django-allauth?

G3W-Suite comes with `django-allauth` preinstalled for social authentication. This implementation uses django-allauth's OpenID Connect provider to integrate with Keycloak, following G3W-Suite's standard patterns.

### Configuration

The Keycloak service is pre-configured with:

- **Keycloak Admin Console**: http://localhost:8180
  - Username: `admin` (configurable via `KEYCLOAK_ADMIN_USER` in `.env`)
  - Password: `admin123` (configurable via `KEYCLOAK_ADMIN_PASSWORD` in `.env`)

- **Realm**: `g3wsuite` (configurable via `KEYCLOAK_REALM` in `.env`)
- **Client ID**: `g3w-suite-client` (configurable via `KEYCLOAK_CLIENT_ID` in `.env`)
- **Database**: Uses the existing PostgreSQL database with a separate `keycloak` schema
- **Authentication**: Managed through django-allauth (no additional packages required)

### Pre-configured Test Users

The realm comes with two pre-configured test users:

1. **Admin User**
   - Username: `admin`
   - Password: `admin123`
   - Email: `admin@g3wsuite.local`
   - Roles: `admin`, `user`

2. **Standard User**
   - Username: `testuser`
   - Password: `testuser123`
   - Email: `testuser@g3wsuite.local`
   - Roles: `user`

### First Time Setup

1. **Start all services** (including Keycloak):
   ```sh
   docker-compose up -d
   ```

2. **Access Keycloak Admin Console** at http://localhost:8180 and verify the realm is imported

3. **Get the client secret** (if not already configured):
   - Login to Keycloak Admin Console
   - Select the `g3wsuite` realm
   - Go to: **Clients** → **g3w-suite-client** → **Credentials** tab
   - Copy the **Client Secret** value
   - Update `KEYCLOAK_CLIENT_SECRET` in your `.env` file

4. **Update redirect URIs** (if using a custom domain):
   - Go to: **Clients** → **g3w-suite-client** → **Settings** tab
   - Update **Valid Redirect URIs** to: `http://your-domain.com:8080/accounts/keycloak/login/callback/`
   - Update **Web Origins** to: `http://your-domain.com:8080`

5. **Restart G3W-Suite** to apply the configuration:
   ```sh
   docker-compose restart g3w-suite
   ```

### Authentication Flow

Once configured, users will:
1. Visit G3W-Suite at http://localhost:8080
2. Click "Login with Keycloak" on the G3W-Suite login page
3. Get redirected to Keycloak authentication page
4. Authenticate with Keycloak credentials
5. Get redirected back to G3W-Suite at `/accounts/keycloak/login/callback/`
6. Automatically logged into G3W-Suite with an active session

**Note**: django-allauth integrates Keycloak as a social login provider, appearing alongside any other configured social authentication methods.

### Managing Users

Add new users via the Keycloak Admin Console:
- **Users** → **Add user**
- Set username, email, first name, last name
- Go to **Credentials** tab and set a password
- Go to **Role Mappings** tab and assign appropriate realm roles

### Database Schema Isolation

Keycloak uses a separate PostgreSQL schema (`keycloak`) within the same database:
- **G3W-Suite data**: `public` schema
- **Keycloak data**: `keycloak` schema
- Both schemas use the same PostgreSQL user for simplicity

### Troubleshooting

**Issue**: Keycloak redirect fails
- Verify `WEBGIS_PUBLIC_HOSTNAME` in `.env` matches your actual domain
- Check that redirect URIs in Keycloak client settings include your domain
- Ensure nginx is proxying `/auth/` to Keycloak (see `config/nginx/locations`)

**Issue**: Users can't login
- Verify the client secret matches in both Keycloak and `.env`
- Check Keycloak logs: `docker-compose logs keycloak`
- Check G3W-Suite logs: `docker-compose logs g3w-suite`

**Issue**: Database connection errors
- Verify the `keycloak` schema exists in PostgreSQL
- Check PostgreSQL logs: `docker-compose logs postgis`
- Manually create schema if needed: `docker-compose exec postgis psql -U g3wsuite -d g3wsuite -c "CREATE SCHEMA IF NOT EXISTS keycloak;"`

### Disabling Keycloak (Fallback to Django Auth)

To temporarily disable Keycloak SSO and use only Django's built-in authentication:

1. Edit `config/g3w-suite/settings_docker.py`
2. Comment out the Keycloak provider in `G3WADMIN_LOCAL_MORE_APPS`:
   ```python
   G3WADMIN_LOCAL_MORE_APPS = [
       # 'allauth.socialaccount.providers.openid_connect',  # Comment this line
       'caching',
       'editing',
       # ... other apps
   ]
   ```
3. Restart G3W-Suite: `docker-compose restart g3w-suite`

**Note**: Django's standard authentication will still be available. Users can log in with Django admin credentials even when Keycloak is enabled.

### Role Mapping from Keycloak to G3W-Suite

This deployment implements **semi-automatic admin role assignment** based on Keycloak roles:

#### How It Works

**Custom Adapter:** `config/g3w-suite/custom_adapter.py`
- Extends G3W-Suite's built-in social account adapter
- Automatically grants admin interface access to users with Keycloak 'admin' role
- Requires manual approval for full superuser permissions (security best practice)

#### Role Assignment Logic

| Keycloak Role | Django Permissions | G3W-Suite Access |
|---------------|-------------------|------------------|
| `admin` | `is_staff=True`<br>`is_superuser=False` (requires manual approval) | Can access admin interface<br>Limited permissions until superuser granted |
| `user` | Standard G3W role via `SOCIALACCOUNT_USER_ROLE` | Editor/Viewer level access |

#### Granting Full Superuser Permissions

After a user with Keycloak 'admin' role logs in:

1. **Check Logs:** `docker-compose logs g3w-suite | grep "ADMIN INTERFACE ACCESS GRANTED"`
2. **Verify:** User has `is_staff=True` but `is_superuser=False`
3. **Grant Superuser (choose one method):**

   **Via Django Admin:**
   ```bash
   # Login to Django admin at http://localhost:8080/admin/
   # Users > [select user] > Check "Superuser status" > Save
   ```

   **Via Database:**
   ```bash
   docker-compose exec postgis bash -c "PGPASSWORD='89#kL8y3D' psql -h 127.0.0.1 -U g3wsuite -d g3wsuite -c \"UPDATE auth_user SET is_superuser=true WHERE email='admin@g3wsuite.local';\""
   ```

   **Via Django Shell:**
   ```bash
   docker-compose exec g3w-suite bash -c "cd /code/g3w-admin && python3 manage.py shell -c \"from django.contrib.auth.models import User; u=User.objects.get(email='admin@g3wsuite.local'); u.is_superuser=True; u.save(); print('Superuser granted')\""
   ```

#### Security Rationale

**Why Semi-Automatic?**

- **Audit Trail:** All admin access requests are logged
- **Separation of Duties:** Keycloak admin ≠ automatic G3W superuser
- **Manual Approval:** Prevents unauthorized privilege escalation
- **Defense in Depth:** Two-step process adds security layer

**Trust Boundary:**
- Keycloak manages authentication (who you are)
- G3W-Suite manages authorization (what you can do)
- Admin promotion requires action in G3W-Suite domain

#### Pre-configured Test Users

The realm includes two test users:

1. **admin@g3wsuite.local** (password: `admin123`)
   - Keycloak roles: `admin`, `user`
   - Will get `is_staff=True` automatically
   - Requires manual `is_superuser=True` grant

2. **testuser@g3wsuite.local** (password: `testuser123`)
   - Keycloak roles: `user`
   - Gets standard G3W role (default: Viewer Level 1)
   - No admin interface access

#### Customizing Role Mapping

To modify the role mapping behavior, edit `config/g3w-suite/custom_adapter.py`:

```python
def save_user(self, request, sociallogin, form=None):
    user = super().save_user(request, sociallogin, form)
    keycloak_roles = self._get_keycloak_roles(sociallogin)

    # Customize this logic:
    if 'admin' in keycloak_roles:
        user.is_staff = True
        user.save()

    return user
```

**Configuration Files:**
- Custom adapter: `config/g3w-suite/custom_adapter.py`
- Settings reference: `config/g3w-suite/settings_docker.py` (line 278-287)
- Keycloak roles: `config/keycloak/realm-export.json` (line 132-144)

## 💻 How to access into a container 

1. login into a service

```sh
$ make run-postgis ENV=prod

# make run-g3w-suite ENV=prod
# make run-nginx ENV=prod
# make run-redis ENV=prod
```

2. perform your administrative tasks (eg. connect to postgis as "postgres" user):

```sh
root@84ef6a8d23e6:/# su - postgres

postgres@84ef6a8d23e6:~$ psql
psql (11.2 (Debian 11.2-1.pgdg90+1))
Type "help" for help.

postgres=#
```

## 🔒 HTTPS

To enable https with LetsEncrypt::

- uncomment ssl section within `config/nginx/nginx.conf`
- update `WEBGIS_PUBLIC_HOSTNAME` environment variable within the `.env` and `config/nginx/nginx.conf` files
- launch `sudo make renew-ssl`
- make sure the certs are renewed by adding a cron job with `sudo crontab -e` and add the following line:
  `0 3 * * * /<path_to_your_docker_files>/run_certbot.sh`

## 📦 Docker image

Docker compose will usually download images from: https://hub.docker.com/u/g3wsuite 

A custom (local) docker image for the suite can be created with:

```bash
docker build -f Dockerfile.g3wsuite.dockerfile -t g3wsuite/g3w-suite:dev --no-cache .

# OPTIONAL:
# docker build -f Dockerfile.g3wsuite-deps.ltr.dockerfile -t g3wsuite/g3w-suite-deps-ltr:dev --no-cache .
```

The image is build on latest Ubuntu and QGIS LTR, following this execution order:

1. [Dockerfile.g3wsuite-deps.ltr.dockerfile](./Dockerfile.g3wsuite-deps.ltr.dockerfile) ← installs Ubuntu and QGIS LTR
2. [Dockerfile.g3wsuite.dockerfile](./Dockerfile.g3wsuite.dockerfile)  ← run "setup.sh" and "docker-entrypoint.sh"
3. [scripts/setup.sh](./scripts/setup.sh) ← install g3w-admin and some other python plugins
4. [scripts/docker-entrypoint.sh](./scripts/docker-entrypoint.sh) ← start gunicorn

## 🎨 Style customization

- custom templates folder: `config/g3w-suite/overrides/templates` → a Docker service restart is required to make the changes effective.
- custom logo (see: [docs](https://g3w-suite.readthedocs.io/en/latest/settings.html#general-layout-settings)): `config/g3w-suite/settings_docker.py` → a Docker service restart is required to make the changes effective.
- custom CSS: `config/g3w-suite/overrides/static/style.css` → changes are effective immediately

## 🚀 Performance optimizations

1. set scale-dependent visibility for the entire layer or for some filtered features (example: show only major roads until at scale 1:1E+6)
2. when using rule-based/categorized classification or scale-dependent visibility create indexes on the column(s) involved in the rule expression (example: "create index idx_elec_penwell_ious on elec_penwell_ious (owner);" )
3. start the project with only a few layers turned on by default
4. do not turn on by default base-layers XYZ such as (Google base maps)
5. do not use rule-based/categorized rendering on layers with too many categories (example: elec_penwell_public_power), they are unreadable anyway
6. enable redering simplification for not-point layers, set it to `Distance` `1.2` and check `Enable provider simplification if available`
7. enable cache on linestring and polygon layers (tile cache can be configured and cleared per-layer through the webgis admin panel and lasts forever until it is disabled or cleared)
8. set a cron job on host machine that checks edited features that have been locked for more than 4 hours and frees them:
```
0 */1 * * * docker exec g3w-suite-docker_g3w-suite_1 python3 /code/g3w-admin/manage.py check_features_locked
```

## 🐋 Portainer usage

Portainer (https://www.portainer.io) is a docker-based web application used to edit and manage Docker applications in a simple and intuitive way.

Plese refer to the [Add new stack](https://docs.portainer.io/user/docker/stacks/add) section to learn how to deploy the `docker-compose-consumer.yml` stack with Portainer (>= v2.1.1).


## ♻️ Database backup / restore 

```sh
# NB:
# • (ENV = dev)      → docker-compose-dev.yml
# • (ENV = prod)     → docker-compose.yml
# • (ENV = consumer) → docker-compose-consumer.yml

docker compose up -f docker-compose.yml up -d

make backup-db ID=foo-backup ENV=prod
make restore-db ID=foo-backup ENV=prod
```

### Contributors

* GIS3W: [wlorenzetti](https://github.com/wlorenzetti), [raruto](https://github.com/Raruto)
* ItOpen: [elpaso](https://github.com/elpaso)
* Kartoza: [NyakudyaA](https://github.com/NyakudyaA)
* QTIBIA: [tudorbarascu](https://github.com/tudorbarascu)
