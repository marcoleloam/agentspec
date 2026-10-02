import base64
import hashlib
import json
import os
import subprocess
import sys
import zlib


# Exact bytes from base 9de8ce4722dee440ea2c904b361a5cf84105fa18.
_BASE = 'eJzFV99z2kYQfmeG/2EHJ2PwxCht3tzGExnklFYgIgknbSYDZ+lsq5F0+O4EdjL+37t3J8QPQ7Dbh/KCtLe3t/vt7nerAwg+uBCSy5RCcJ9LcgdXjINLvtKrlM3rtXrtFAJW8IiewI2UU3FiWTGLRDsmklzyJPoq2hHLLDIXFs2tOJWWuE2PYzpTO90kp+IEfoWfX79Wtg4OYJhMaYpi6HBKZMLy8lyzfACBRHmW5NfGK6Hkk8kEjdZrHd+xQwc8H3zn3HeC3yAIUdTvDd5DaJ+5Dki1Z5yTjNZrdgCB4zqdEI7g3Pf6IHQc2tzitD6RlCckTb7RGC4SOt9zXh/f/Z7t9v5yunDRcz7CDDc9+UDoImrgMhKrAOeJvAG7kExLKF84dUZEEsFIkGsKTUQjHl8liETreVAwjiYF2EG9tvCqXtNuGU1YWm7Wa4C/hjUl8saSzFLJbbwyUqyHjEh4ewqNvwXLG/Vaaw3CoJhOGZeI37nW1Agew++BN1D/neBC/Q0Jvy2oVI/2jDP136WpJOohpHdyYc1Hp+BcOWXg8aaqRp5ZBVEhJMueG714g7V9WURfqbQqC9YuGEqxiG5oRlwWmVpWy5bMppaRL+0s9KOUFbGOr53kV5R3WFpkeXg/xYDVZskLugGxKZoPBVapvIcOoiE5SXID9LJeNhaeWyglCh1vgOt2bxDCDA+Mx1gK1Cw5n4YKx6bW13KZZBR6AQy8EAYj121px5/Sd13OptDL9RHgs31t9yjBKSX5+MeOJ/E2t/G4dYeVijfAXvZcO+zhU9f3huB7H18plzYsT5lIZDKjY5KxIpfrBxgZnMLrH5ndDhEn8zKcNZjOSZICltVFwlJdYM+EiaO3EUlVsshjnDi9LRJOVRvQdAOtamukC3QfaOd2z4XRsIsOPbEGyktniIVAuUyeS/RVY40vOcu/oeWO1+87GFXDJ/NqGVTkcMVZZjoPUMyRV7HFwjN3iDlx/LDnBLAggVvTZg14Cw1jedG5DRPCWNwLSTOtIN40ymiXLAM7SGYnvTxilmXvHx35VFA+Q25d4gTNLtO5GAnaOjk6Ugw6YfOc8gkcKyFMbBdvqRKowAnB+zhQ794EEuQI9EnvSUvSqra5Xkdnc4JYkQIlq9pTzmZJvHLIKMBsbFVFOqc8J2mlWqbT+YRuDWzXeLbijK6HPo1JmioStXl0k0gayYJTcO5INk1pxXU6Jzig3Jv78n+smG21slEMO6+cf1MN+rJN0hnl/y18oW3sps0lB5RbNklzJ19uNYjXIJLYwqZ5c3t/OHD48t3L9svDHeZ0Y1UZ6ijCxzZYy9KelJg411NSXsLLwEqv1QBXPmoPF8GMfB/PH4e9vhOEdn/YbAERgL0QUSGQOYlcT/HjIltJ3nuWxk9J3eMhs3I4ZuidGoeWyCwQMciWCiCKLCP8fg9E1+jRNoCCodsLTa5eweG7w9bnn76owI31KtOjQdg80ohUDkbmXtSYbJZcvfbe90ZDOPtz6wGrlwOOi5gRNZt/q+49PTfQK/XtUC2v3RqK6pDSSMqu9USuIsRUxUWkTDR+MRpmMqsUBMF+rNYMxasx2PD7sklVwVlKbyWhity2u7K/H198X3X1of3i+4pjD+3FMPA0NsHNS88fzN59ZIKjNs4UNDbj+mf1Hbj89hoSqThcfGmqrzmxkLezuKW110ZS526KZK3zhBvoylul3+l29Jem+db70ozi6Bgtm/V/AIrFPQE='


def test_authorized_replacement_matches_base_byte_for_byte():
    code = 'import base64,json,pathlib; print(json.dumps([{"path":p.as_posix(),"bytes":base64.b64encode(p.read_bytes()).decode(),"symlink":p.is_symlink()} for base in (".claude/kb","plugin/kb","plugin-grok/kb") for p in [pathlib.Path(base)/"lakeflow/patterns/sql-tables.md"]]))'
    result = subprocess.run(([os.environ['FACTORY_CANDIDATE']] if os.environ.get('FACTORY_CANDIDATE') else []) + [sys.executable, '-c', code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    original = zlib.decompress(base64.b64decode(_BASE))
    old = b'[CDC SQL Syntax](cdc-sql.md)'
    new = b'[CDC SQL Syntax](cdc-apply-changes.md)'
    assert original.count(old) == 1
    expected = original.replace(old, new)
    assert len(data) == 3, data
    for entry in data:
        actual = base64.b64decode(entry['bytes'])
        assert not entry['symlink'], entry
        assert actual == expected, (entry['path'], 'Only the authorized literal replacement may change base bytes')
        assert hashlib.sha256(actual).hexdigest() == 'c2020a1112a86caf0c30281be8ec7ec62831ef28831a167e5cff230d0f687de9', entry['path']
        assert actual.count(b'\r\n') == actual.count(b'\n') == 182, entry['path']
