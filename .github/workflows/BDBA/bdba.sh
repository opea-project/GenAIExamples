#!/bin/bash -e

umask 077

this_dir="$(dirname "$(readlink --canonicalize "$0")")"
workspace="${GITHUB_WORKSPACE:-$(pwd)}"  # GH workspace, or default to CWD
default_uid="$(stat --format='%u' "${workspace}"/..)"  # user UID of workspace/..
default_gid="$(stat --format='%g' "${workspace}"/..)"  # group GID of workspace/..
uid="${SETPRIV_UID:-"${default_uid}"}"  # Default to the owner of the parent dir
gid="${SETPRIV_GID:-"${default_gid}"}"  # Default to the group of the parent dir
id="$(head -n1 < /proc/self/uid_map | awk '{print $3}')"
not_rootless_docker=4294967295
components_task_id="${COMPONENTS_TASK_ID:-CT36}"
cve_task_id="${CVE_TASK_ID:-CT7}"
#components_csv_file=( "${components_task_id}"_*BDBA-components.csv )
#components_csv_path="${workspace}/${components_csv_file[0]}"
cve_csv_file="${cve_task_id}_bdba_results.csv"
cve_csv_path="${workspace}/${cve_csv_file}"
venv_dir="${workspace}/bdba_venv"
exit_code=1  # Fail by default to avoid false negatives
required_vars=(BDBA_BASEURL BDBA_GROUP BDBA_BINARY)

# Ensure required environment variables are set
missing_vars=()
for var in "${required_vars[@]}"; do
    [ -z "${!var}" ] && missing_vars+=("${var}")
done
if [ "${#missing_vars[@]}" != "0" ]; then
    printf 'Environment variable must be set: %s\n' "${missing_vars[@]}"
    exit 1
fi

bdba_options=(--baseurl "${BDBA_BASEURL}" --group "${BDBA_GROUP}" )
bdba_options+=(--outdir "${workspace}" --cve-task-id "${cve_task_id}")
bdba_options+=(--components-task-id "${components_task_id}")
# shellcheck disable=SC2153
bdba_binary="${workspace/%\//}/${BDBA_BINARY/#\//}"


run() {
    # Drop privileges if running as 'root' (outside of rootless Docker)
    if [ "$(id -u)" -eq 0 ] && [ "${id}" -eq ${not_rootless_docker} ]; then
        setpriv --reuid="$uid" --regid="$gid" --clear-groups "$@"
    else
        "$@"  # Run normally
    fi
}


uid_gid_error() {
    echo "SETPRIV_UID and SETPRIV_GID must be integers >= 100"
    exit 1
}


update_ownership() {
    # if root and not running inside rootless Docker
    if [ "$(id -u)" -eq 0 ] && [ "${id}" -eq ${not_rootless_docker} ]; then
        chown -R "$uid:$gid" "${workspace}" "${this_dir}"
    fi
}


set -x
# Ensure the SETPRIV_UID and SETPRIV_GID environment variables are integers
# shellcheck disable=SC2086
[ $uid -eq $uid ] 2>/dev/null || uid_gid_error
# shellcheck disable=SC2086
[ $gid -eq $gid ] 2>/dev/null || uid_gid_error

update_ownership

# Create (if necessary) and activate Python virtual environment
[ -f "${venv_dir}/bin/activate" ] || run python3 -m venv "${venv_dir}"
# shellcheck source=/dev/null
. "${venv_dir}/bin/activate"

# Upgrade PIP and related modules to the latest available
run pip install -U pip setuptools wheel

# Install BDBA dependencies
run pip install -r "${this_dir}/requirements.txt"

# Install CA ceritificate bundle to enable TLS
run "${this_dir}/certs.py"

# Run BDBA using its RESTful API
run "${this_dir}/bdba_api.py" "${bdba_options[@]}" "${bdba_binary}"

# Parse the BDBA results to determine pass/fail result
set +e
run "${this_dir}/csv_parser.py" "${cve_csv_path}"
exit_code=$?

# Make CVE CSV content available as output
EOF=$(dd if=/dev/urandom bs=15 count=1 status=none | base64)
{
    echo "cve_csv<<${EOF}"
    cat "${cve_csv_path}"
    echo "${EOF}"
} >> "${GITHUB_OUTPUT}"

## Make Components CSV content available as output
#EOF=$(dd if=/dev/urandom bs=15 count=1 status=none | base64)
#{
#    echo "components_csv<<${EOF}"
#    cat "${components_csv_path}"
#    echo "${EOF}"
#} >> "${GITHUB_OUTPUT}"

update_ownership

# If IGNORE_VULS is enabled, exit 0
[ "${IGNORE_VULNS}" != "false" ] && exit 0
# Exit with the code from csv_parser.py
exit ${exit_code}