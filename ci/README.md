# GitHub Actions workflow — currently parked here

`github-actions-ci.yml` is the project's CI definition. It lives in `ci/`
rather than `.github/workflows/` for one reason only: pushing a file under
`.github/workflows/` requires the **workflows** permission, and the GitHub App
used to publish this branch does not have it, so the push was rejected with:

```
refusing to allow a GitHub App to create or update workflow
`.github/workflows/ci.yml` without `workflows` permission
```

Parking it here keeps the deploy unblocked without losing the file.

## To activate it

Grant the integration the **Workflows: Read and write** permission
(repo → Settings → Actions → General, or the App's repository permissions),
then:

```bash
mkdir -p .github/workflows
git mv ci/github-actions-ci.yml .github/workflows/ci.yml
git commit -m "Restore GitHub Actions CI"
git push
```

## Worth knowing

This workflow runs `python manage.py seed_demo`. That step would have caught
the `NameError` on `hk2` and `team` that was breaking `render_start.sh` on
Render — but CI never executed, because `main` contained only `PP_latest.zip`
and no `requirements.txt` for the workflow to install from. Restoring it now
that the project is a real tree gives you a genuine regression net.
