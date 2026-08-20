{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "b669270d-8175-4a1c-bb2c-7e8b76535c59",
   "metadata": {},
   "outputs": [],
   "source": [
    "def estimate_trip_cost(days, hotel_pref):\n",
    "\n",
    "    hotel_cost = {\n",
    "        \"Budget / Hostel\": 1200,\n",
    "        \"3 Star\": 3000,\n",
    "        \"4 Star\": 6000,\n",
    "        \"5 Star\": 12000\n",
    "    }\n",
    "\n",
    "    stay = hotel_cost.get(hotel_pref, 3000) * days\n",
    "\n",
    "    food = 800 * days\n",
    "\n",
    "    local_transport = 500 * days\n",
    "\n",
    "    attraction = 300 * days\n",
    "\n",
    "    total = stay + food + local_transport + attraction\n",
    "\n",
    "    return {\n",
    "        \"stay\": stay,\n",
    "        \"food\": food,\n",
    "        \"transport\": local_transport,\n",
    "        \"tickets\": attraction,\n",
    "        \"total\": total\n",
    "    }"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python (TripSense)",
   "language": "python",
   "name": "tripsense"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.19"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
