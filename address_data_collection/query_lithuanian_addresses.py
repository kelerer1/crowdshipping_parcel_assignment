import requests
import pandas as pd
import random


LAYERS = {
    "Vilnius": (
        "https://zemelapiai.vplanas.lt/arcgis/rest/services/"
        "Open_Data/Adresiniai_taskai_OD/MapServer/0"
    ),
    "Kaunas": (
        "https://digital.kaunas.lt/arcgis/rest/services/"
        "Bendra/Bendri_duomenys/MapServer/2"
    ),
}


def sample_addresses(city, n=2000, seed=42):
    url = LAYERS[city] + "/query"

    with requests.Session() as session:
        def query(**params):
            response = session.get(
                url, params={"f": "json", **params}, timeout=120
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data

        # Retrieve the complete sampling frame, not just the first page.
        result = query(where="1=1", returnIdsOnly="true")
        ids = sorted(set(result.get("objectIds") or []))
        id_field = result["objectIdFieldName"]

        if len(ids) < n:
            raise ValueError(f"{city}: only {len(ids)} records available.")

        selected = random.Random(seed).sample(ids, n)

        # Small batches keep requests below service and URL-size limits.
        records = []
        for start in range(0, n, 100):
            batch = selected[start:start + 100]
            data = query(
                objectIds=",".join(map(str, batch)),
                outFields="*",
                returnGeometry="true",
                outSR=4326,  # Request longitude/latitude.
            )

            if data.get("exceededTransferLimit"):
                raise RuntimeError("Service truncated a batch.")

            for feature in data.get("features", []):
                row = feature["attributes"].copy()
                geometry = feature.get("geometry") or {}
                row["longitude"] = geometry.get("x")
                row["latitude"] = geometry.get("y")
                records.append(row)

    df = pd.DataFrame(records)

    if len(df) != n or df[id_field].nunique() != n:
        raise RuntimeError("Incomplete or duplicate results; rerun the query.")

    if df[["longitude", "latitude"]].isna().any().any():
        raise RuntimeError("Some sampled records lack coordinates.")

    # Preserve the random draw order.
    df = df.set_index(id_field).loc[selected].reset_index()
    df["city"] = city

    #filename = f"{city.lower()}_{n}_addresses.csv"
    # df.to_csv(filename, index=False, encoding="utf-8-sig")
    # print(f"Saved {n} address points to {filename}")
    return df