# reticulum-tools

A collection of utility scripts for [Reticulum](https://reticulum.network) mesh network nodes running [MeshChat](https://github.com/liamcottle/reticulum-meshchat).

## Tools

### auto-prop-node

Automatically selects the best LXMF propagation node for MeshChat and sends you a status report via LXMF message every hour.

**How it works:**

1. Queries the local MeshChat API for all known `lxmf.propagation` announces
2. Filters out disabled nodes and local nodes below `MIN_HOPS`
3. Selects the best candidate by hop count
4. Updates MeshChat's preferred propagation node via the API
5. Sends an LXMF status message to your configured address — whether or not the node changed

**Files:**

| File | Description |
|------|-------------|
| auto_propagation_node.py | Main selector script |
| auto-propnode.service | Systemd oneshot service |
| auto-propnode.timer | Systemd timer — runs on boot (+2min) and hourly |

**Requirements:**

- MeshChat running and accessible at `http://localhost:8000`
- Python venv with `msgpack` installed (included in standard MeshChat venv)

**Setup:**

1. Edit `auto_propagation_node.py` and set your values:

```python
MESHCHAT_URL = "http://localhost:8000"   # adjust port if needed
MIN_HOPS = 2                              # ignore local 1-hop nodes
MY_LXMF_ADDRESS = "YOUR_LXMF_ADDRESS_HASH_HERE"
```

Find your LXMF address with:

```bash
curl -s http://localhost:8000/api/v1/config | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['config']['lxmf_address_hash'])"
```

2. Copy the script to your home directory:

```bash
cp auto_propagation_node.py ~/auto_propagation_node.py
chmod +x ~/auto_propagation_node.py
```

3. Test it manually first:

```bash
~/meshchat-venv/bin/python ~/auto_propagation_node.py
```

4. Install the systemd service and timer:

```bash
sudo cp auto-propnode.service /etc/systemd/system/
sudo cp auto-propnode.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now auto-propnode.timer
```

5. Check the timer is active:

```bash
systemctl status auto-propnode.timer
```

6. View the log:

```bash
tail -f ~/auto_propagation_node.log
```

**Note:** If your MeshChat venv or username differs from the defaults (`~/meshchat-venv`, user `user`), edit the `ExecStart` line in `auto-propnode.service` accordingly.

## Contact

You can reach the author on the Reticulum network via LXMF:

```
9845aed67ab981c008f6c387aa2e97b9
```

## Licence

MIT — see [LICENSE](LICENSE)
